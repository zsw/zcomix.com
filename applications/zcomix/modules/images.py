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
        if request.vars.size and request.vars.size in Resizer.sizes:
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


class Resizer(object):
    """Class representing an image resizer"""
    sizes = {
        # size: (w px, h px)
        'medium': (500, 500),
        'thumb': (150, 150),
    }

    def __init__(self, field, image_name):
        """Constructor

        Args:
            field: gluon.dal.Field instance, eg db.creator.image
            field, image_name: string, the name of the image.
                Eg creator.image.944cdb07605150ca.636875636b5f666f72736d616e2e6a7067.jpg
        """
        self.field = field
        self.image_name = image_name

    def delete(self, size):
        """Delete a version of the image

        Args:
            size: string, name of size, must one of the keys of the cls.sizes
                    dict
        """
        fullname = self.fullname()
        new_fullname = fullname.replace('/original/', '/{s}/'.format(s=size))
        if os.path.exists(new_fullname):
            os.unlink(new_fullname)

    def delete_all(self):
        """Delete all sizes."""
        for size in self.sizes.keys():
            self.delete(size)
        self.delete('original')

    def fullname(self):
        """Return the fullname of the image."""
        db = self.field._db
        unused_file_name, fullname = self.field.retrieve(
            self.image_name,
            nameonly=True,
        )
        return fullname

    def resize(self, size):
        """Resize the image.

        Args:
            size: string, name of size, must one of the keys of the cls.sizes
                    dict
        """
        fullname = self.fullname()
        new_fullname = fullname.replace('/original/', '/{s}/'.format(s=size))
        new_path = os.path.dirname(new_fullname)
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        im = Image.open(fullname)
        im.thumbnail(self.sizes[size], Image.ANTIALIAS)
        im.save(new_fullname)
        return new_fullname

    def resize_all(self):
        """Resize all sizes."""
        for size in self.sizes.keys():
            self.resize(size)


def img_tag(field, size='original'):
    """Return an image HTML tag suitable for an resizeable image.

    Args:
        field: gluon.dal.Field instance, eg db.creator.image
        size: string, the image size
    """
    if not field:
        return IMG(
            _src=URL(
                c='static',
                f='images',
                args='portrait_placeholder.png'
            )
        )

    if size != 'original' and size not in Resizer.sizes.keys():
        size = 'original'

    return IMG(
        _src=URL(
            c='images',
            f='download',
            args=field,
            vars={'size': size},
        )
    )
