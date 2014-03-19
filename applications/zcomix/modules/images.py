#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Classes and functions related to images.
"""
import os
import re
from PIL import Image
from gluon import *
from gluon.globals import Response
from gluon.streamer import DEFAULT_CHUNK_SIZE
from gluon.contenttype import contenttype


class Downloader(Response):
    """Class representing an image downloader"""

    def download(self, request, db, chunk_size=DEFAULT_CHUNK_SIZE, attachment=True, download_filename=None):
        """
        Adapted from Response.download.

        request.vars.size: string, one of 'original' (default), 'medium', or
                'thumb'. If provided the image is streamed from a subdirectory
                 with that name.
        """
        current.session.forget(current.response)

        if not request.args:
            raise HTTP(404)
        name = request.args[-1]
        items = re.compile('(?P<table>.*?)\.(?P<field>.*?)\..*')\
            .match(name)
        if not items:
            raise HTTP(404)
        (t, f) = (items.group('table'), items.group('field'))
        try:
            field = db[t][f]
        except AttributeError:
            raise HTTP(404)
        try:
            (filename, stream) = field.retrieve(name, nameonly=True)
        except IOError:
            raise HTTP(404)

        # Customization: start
        if request.vars.size and request.vars.size in UploadImage.sizes:
            resized = stream.replace('/original/', '/{s}/'.format(s=request.vars.size))
            if os.path.exists(resized):
                stream = resized
        # Customization: end

        headers = self.headers
        headers['Content-Type'] = contenttype(name)
        if download_filename is None:
            download_filename = filename
        if attachment:
            headers['Content-Disposition'] = \
                'attachment; filename="%s"' % download_filename.replace('"', '\"')
        return self.stream(stream, chunk_size=chunk_size, request=request)


class UploadImage(object):
    """Class representing an image resizer"""

    sizes = {
        # size: (w px, h px)
        'medium': (500, 500),
        'thumb': (170, 170),
    }

    thumb_shrink_threshold = 120
    thumb_shrink_multiplier = 0.80

    def __init__(self, field, image_name):
        """Constructor

        Args:
            field: gluon.dal.Field instance, eg db.creator.image
            field, image_name: string, the name of the image.
                Eg creator.image.944cdb07605150ca.636875636b5f666f72736d616e2e6a7067.jpg
        """
        self.field = field
        self.image_name = image_name
        self._images = {}               # {'size': Image instance}
        self._dimensions = {}           # {'size': (w, h)}

    def delete(self, size):
        """Delete a version of the image

        Args:
            size: string, name of size, must one of the keys of the cls.sizes
                    dict
        """
        fullname = self.fullname(size=size)
        if os.path.exists(fullname):
            os.unlink(fullname)

    def delete_all(self):
        """Delete all sizes."""
        for size in self.sizes.keys():
            self.delete(size)
        self.delete('original')

    def dimensions(self, size='original'):
        """Return the dimensions of the image of the indicated size.

        Args:
            size: string, name of size, must one of the keys of the cls.sizes
                    dict
        """
        if not self._dimensions or size not in self._dimensions:
            im = self.pil_image(size=size)
            if im:
                self._dimensions[size] = im.size
            else:
                self._dimensions[size] = None
        return self._dimensions[size]

    def fullname(self, size='original'):
        """Return the fullname of the image."""
        unused_file_name, fullname = self.field.retrieve(
            self.image_name,
            nameonly=True,
        )
        if size != 'original':
            fullname = fullname.replace('/original/', '/{s}/'.format(s=size))
        return fullname

    def pil_image(self, size='original'):
        """Return a PIL Image instance representing the image.

        Args:
            size: string, name of size, must one of the keys of the cls.sizes
                    dict
        """
        if not self._images or size not in self._images:
            filename = self.fullname(size=size)
            if os.path.exists(filename):
                self._images[size] = Image.open(filename)
            else:
                self._images[size] = None
        return self._images[size]

    def resize(self, size):
        """Resize the image.

        Args:
            size: string, name of size, must one of the keys of the cls.sizes
                    dict
        """
        original_filename = self.fullname(size='original')
        sized_filename = self.fullname(size=size)
        sized_path = os.path.dirname(sized_filename)
        if not os.path.exists(sized_path):
            os.makedirs(sized_path)
        im = Image.open(original_filename)
        im.thumbnail(self.sizes[size], Image.ANTIALIAS)
        im.save(sized_filename)
        # self.dimensions[size] = im.size
        return sized_filename

    def resize_all(self):
        """Resize all sizes."""
        for size in self.sizes.keys():
            self.resize(size)


def img_tag(field, size='original', img_attributes=None):
    """Return an image HTML tag suitable for an resizeable image.

    Args:
        field: gluon.dal.Field instance, eg db.creator.image
        size: string, the image size
        img_attributes: dict, passed on as IMG(**img_attributes)
    """
    attributes = {}

    if field:
        tag = IMG
        if size != 'original' and size not in UploadImage.sizes.keys():
            size = 'original'

        attributes.update(dict(
            _src=URL(
                c='images',
                f='download',
                args=field,
                vars={'size': size},
            ),
        ))
    else:
        tag = DIV

    if img_attributes:
        attributes.update(img_attributes)

    if not field:
        class_name = 'placeholder_170x170' \
            if size == 'thumb' else 'portrait_placeholder'
        if '_class' in attributes:
            attributes['_class'] = '{c1} {c2}'.format(
                c1=attributes['_class'],
                c2=class_name
            ).replace('img-responsive', '').strip()
        else:
            attributes['_class'] = class_name

    return tag(**attributes)


def set_thumb_dimensions(db, book_page_id, dimensions):
    """Set the db.book_page.thumb_* dimension values for a page.

    Args:
        db: gluon.dal.Dal instance.
        book_page_id: integer, id of book_page record
        dimensions: tuple (w, h), dimensions of thumb image.
    """
    if not dimensions:
        return
    w = dimensions[0]
    h = dimensions[1]
    shrink = True if h > UploadImage.thumb_shrink_threshold \
        and w > UploadImage.thumb_shrink_threshold \
        else False

    thumb_shrink = UploadImage.thumb_shrink_multiplier if shrink else 1

    db(db.book_page.id == book_page_id).update(
        thumb_w=w,
        thumb_h=h,
        thumb_shrink=thumb_shrink
    )
    db.commit()
