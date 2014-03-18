#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Test suite for zcomix/modules/utils.py

"""
import os
import shutil
import sys
import unittest
from BeautifulSoup import BeautifulSoup
from PIL import Image
from cStringIO import StringIO
from gluon import *
from gluon.http import HTTP
from applications.zcomix.modules.images import \
    Downloader, \
    UploadImage, \
    img_tag, \
    set_thumb_dimensions
from applications.zcomix.modules.test_runner import LocalTestCase

# C0111: Missing docstring
# R0904: Too many public methods
# pylint: disable=C0111,R0904


class ImageTestCase(LocalTestCase):
    """ Base class for Image test cases. Sets up test data."""

    _creator = None
    _image_dir = '/tmp/image_resizer'
    _image_original = os.path.join(_image_dir, 'original')
    _image_name = 'file.jpg'
    _uuid_key = None

    _objects = []

    # C0103: *Invalid name "%s" (should match %s)*
    # pylint: disable=C0103
    @classmethod
    def setUp(cls):
        if not os.path.exists(cls._image_original):
            os.makedirs(cls._image_original)

        image_filename = os.path.join(cls._image_dir, cls._image_name)

        # Create an image to test with.
        im = Image.new('RGB', (1200, 1200))
        with open(image_filename, 'wb') as f:
            im.save(f)

        # Store the image in the uploads/original directory
        db.creator.image.uploadfolder = cls._image_original
        with open(image_filename, 'rb') as f:
            stored_filename = db.creator.image.store(f)

        # Create a creator and set the image
        creator_id = db.creator.insert(
            name='Image UploadImage',
            email='resizer@example.com',
            image=stored_filename,
        )
        db.commit()

        cls._creator = db(db.creator.id == creator_id).select().first()
        cls._objects.append(cls._creator)

        cls._uuid_key = cls._creator.image.split('.')[2][:2]

    @classmethod
    def tearDown(cls):
        if os.path.exists(cls._image_dir):
            shutil.rmtree(cls._image_dir)


class TestDownloader(ImageTestCase):

    def test__download(self):
        downloader = Downloader()
        self.assertTrue(downloader)
        env = globals()
        request = env['request']
        request.args = [self._creator.image]

        lengths = {
            # size: bytes
            'original': 23127,
            'medium': 4723,
            'thumb': 1111,
        }

        def test_http(expect_size):
            try:
                stream = downloader.download(request, db)
            except HTTP as http:
                self.assertEqual(http.status, 200)
                self.assertEqual(http.headers['Content-Type'], 'image/jpeg')
                self.assertEqual(http.headers['Content-Disposition'], 'attachment; filename="file.jpg"')
                self.assertEqual(http.headers['Content-Length'], lengths[expect_size])

        test_http('original')

        # Image not resized, should default to original
        request.vars.size = 'medium'
        test_http('original')
        request.vars.size = 'thumb'
        test_http('original')

        resizer = UploadImage(db.creator.image, self._creator.image)
        resizer.resize_all()

        request.vars.size = None
        test_http('original')
        request.vars.size = 'medium'
        test_http('medium')
        request.vars.size = 'thumb'
        test_http('thumb')


class TestUploadImage(ImageTestCase):

    def _exist(self, have=None, have_not=None):
        """Test if image files exist"""
        if have is None:
            have = []
        if have_not is None:
            have_not = []
        unused_filename, original_fullname = db.creator.image.retrieve(
            self._creator.image,
            nameonly=True,
        )
        for size in have:
            file_name = original_fullname.replace('/original/', '/{s}/'.format(s=size))
            self.assertTrue(os.path.exists(file_name))
        for size in have_not:
            file_name = original_fullname.replace('/original/', '/{s}/'.format(s=size))
            self.assertTrue(not os.path.exists(file_name))

    def test____init__(self):
        resizer = UploadImage(db.creator.image, self._image_name)
        self.assertTrue(resizer)
        file_name, fullname = db.creator.image.retrieve(
            self._creator.image,
            nameonly=True,
        )
        self.assertEqual(self._image_name, file_name)
        self.assertEqual(resizer._images, {})
        self.assertEqual(resizer._dimensions, {})

    def test__delete(self):
        resizer = UploadImage(db.creator.image, self._creator.image)
        resizer.resize_all()

        self._exist(have=['original', 'medium', 'thumb'])
        resizer.delete('medium')
        self._exist(have=['original', 'thumb'], have_not=['medium'])
        resizer.delete('thumb')
        self._exist(have=['original'], have_not=['medium', 'thumb'])
        resizer.delete('thumb')     # Handle subsequent delete gracefully
        self._exist(have=['original'], have_not=['medium', 'thumb'])
        resizer.delete('original')
        self._exist(have_not=['original', 'medium', 'thumb'])

    def test__delete_all(self):
        resizer = UploadImage(db.creator.image, self._creator.image)
        resizer.resize_all()

        self._exist(have=['original', 'medium', 'thumb'])
        resizer.delete_all()
        self._exist(have_not=['original', 'medium', 'thumb'])
        resizer.delete_all()        # Handle subsequent delete gracefully
        self._exist(have_not=['original', 'medium', 'thumb'])

    def test__dimensions(self):
        resizer = UploadImage(db.creator.image, self._creator.image)
        self.assertEqual(resizer._dimensions, {})

        dims = resizer.dimensions()
        self.assertTrue('original' in resizer._dimensions)
        self.assertEqual(dims, resizer._dimensions['original'])

        # Should get from cache.
        resizer._dimensions['original'] = (1, 1)
        dims_2 = resizer.dimensions()
        self.assertEqual(dims_2, (1, 1))

        dims_3 = resizer.dimensions(size='medium')
        self.assertTrue('medium' in resizer._dimensions)
        self.assertEqual(dims_3, None)

        medium = resizer.resize('medium')
        dims_4 = resizer.dimensions(size='medium')
        self.assertEqual(dims_4, (500, 500))

    def test__fullname(self):
        resizer = UploadImage(db.creator.image, self._creator.image)
        self.assertEqual(
            resizer.fullname(),
            '/tmp/image_resizer/original/creator.image/{u}/{i}'.format(
                u=self._uuid_key,
                i=self._creator.image,
            ),
        )
        self.assertEqual(
            resizer.fullname(size='medium'),
            '/tmp/image_resizer/medium/creator.image/{u}/{i}'.format(
                u=self._uuid_key,
                i=self._creator.image,
            ),
        )
        self.assertEqual(
            resizer.fullname(size='_fake_'),
            '/tmp/image_resizer/_fake_/creator.image/{u}/{i}'.format(
                u=self._uuid_key,
                i=self._creator.image,
            ),
        )

    def test__pil_image(self):
        resizer = UploadImage(db.creator.image, self._creator.image)
        self.assertEqual(resizer._images, {})

        im = resizer.pil_image()
        self.assertTrue('original' in resizer._images)
        self.assertEqual(im, resizer._images['original'])

        # Should get from cache.
        resizer._images['original'] = '_stub_'
        im_2 = resizer.pil_image()
        self.assertEqual(im_2, resizer._images['original'])

        im_3 = resizer.pil_image(size='medium')
        self.assertTrue('medium' in resizer._images)
        self.assertEqual(im_3, None)

        medium = resizer.resize('medium')
        im_4 = resizer.pil_image(size='medium')
        self.assertEqual(im_4, resizer._images['medium'])

    def test__resize(self):
        resizer = UploadImage(db.creator.image, self._creator.image)
        medium = resizer.resize('medium')
        im = Image.open(medium)
        self.assertEqual(im.size, UploadImage.sizes['medium'])
        thumb = resizer.resize('thumb')
        im = Image.open(thumb)
        self.assertEqual(im.size, UploadImage.sizes['thumb'])

    def test__resize_all(self):
        resizer = UploadImage(db.creator.image, self._creator.image)
        resizer.resize_all()
        unused_filename, original_fullname = db.creator.image.retrieve(
            self._creator.image,
            nameonly=True,
        )
        for size in ['medium', 'thumb']:
            file_name = original_fullname.replace('/original/', '/{s}/'.format(s=size))
            self.assertTrue(os.path.exists(file_name))


class TestFunctions(LocalTestCase):

    def test__img_tag(self):
        def has_attr(tag, attr, value):
            soup = BeautifulSoup(str(tag))
            img = soup.find('img')
            self.assertEqual(img[attr], value)

        tag = img_tag(None)
        has_attr(tag, 'src', '/zcomix/static/images/portrait_placeholder.png')

        tag = img_tag(db.creator.image, size='original')
        has_attr(tag, 'src', '/images/download?size=original')

        tag = img_tag(db.creator.image, size='thumb')
        has_attr(tag, 'src', '/images/download?size=thumb')

        tag = img_tag(db.creator.image, size='_fake_')
        has_attr(tag, 'src', '/images/download?size=original')

        # Test img_attributes parameter
        attrs = dict(_class='img_class', _id='img_id', _style='height: 1px;')
        tag = img_tag(db.creator.image, img_attributes=attrs)
        has_attr(tag, 'src', '/images/download?size=original')
        has_attr(tag, 'class', 'img_class')
        has_attr(tag, 'id', 'img_id')
        has_attr(tag, 'style', 'height: 1px;')

        # If _src is among img_attributes, it should supercede.
        attrs = dict(_src='http://www.src.com', _id='img_id')
        tag = img_tag(db.creator.image, img_attributes=attrs)
        has_attr(tag, 'src', 'http://www.src.com')
        has_attr(tag, 'id', 'img_id')

    def test__set_thumb_dimensions(self):
        book_page_id = db.book_page.insert(
            page_no=1,
            thumb_w=0,
            thumb_h=0,
            thumb_shrink=0,
        )
        db.commit()
        book_page = db(db.book_page.id == book_page_id).select().first()
        self._objects.append(book_page)

        tests = [
            # dimensions, expect
            ((170, 170), 0.80),
            ((170, 121), 0.80),
            ((170, 120), 1),
            ((121, 170), 0.80),
            ((120, 170), 1),
            ((120, 120), 1),
            ((121, 121), 0.80),
        ]

        for t in tests:
            set_thumb_dimensions(db, book_page.id, t[0])
            book_page = db(db.book_page.id == book_page_id).select().first()
            self.assertEqual(book_page.thumb_w, t[0][0])
            self.assertEqual(book_page.thumb_h, t[0][1])
            self.assertEqual(book_page.thumb_shrink, t[1])


def setUpModule():
    """Set up web2py environment."""
    # C0103: *Invalid name "%%s" (should match %%s)*
    # pylint: disable=C0103
    LocalTestCase.set_env(globals())


if __name__ == '__main__':
    unittest.main()
