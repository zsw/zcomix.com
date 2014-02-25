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
    Resizer, \
    img_tag
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
            name='Image Resizer',
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
            'thumb': 1027,
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

        resizer = Resizer(db.creator.image, self._creator.image)
        resizer.resize_all()

        request.vars.size = None
        test_http('original')
        request.vars.size = 'medium'
        test_http('medium')
        request.vars.size = 'thumb'
        test_http('thumb')


class TestResizer(ImageTestCase):

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
        resizer = Resizer(db.creator.image, self._image_name)
        self.assertTrue(resizer)
        file_name, fullname = db.creator.image.retrieve(
            self._creator.image,
            nameonly=True,
        )
        self.assertEqual(self._image_name, file_name)

    def test__delete(self):
        resizer = Resizer(db.creator.image, self._creator.image)
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
        resizer = Resizer(db.creator.image, self._creator.image)
        resizer.resize_all()

        self._exist(have=['original', 'medium', 'thumb'])
        resizer.delete_all()
        self._exist(have_not=['original', 'medium', 'thumb'])
        resizer.delete_all()        # Handle subsequent delete gracefully
        self._exist(have_not=['original', 'medium', 'thumb'])

    def test__fullname(self):
        resizer = Resizer(db.creator.image, self._creator.image)
        self.assertEqual(
            resizer.fullname(),
            '/tmp/image_resizer/original/creator.image/{u}/{i}'.format(
                u=self._uuid_key,
                i=self._creator.image,
            ),
        )

    def test__resize(self):
        resizer = Resizer(db.creator.image, self._creator.image)
        medium = resizer.resize('medium')
        im = Image.open(medium)
        self.assertEqual(im.size, Resizer.sizes['medium'])
        thumb = resizer.resize('thumb')
        im = Image.open(thumb)
        self.assertEqual(im.size, Resizer.sizes['thumb'])

    def test__resize_all(self):
        resizer = Resizer(db.creator.image, self._creator.image)
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
        def has_src(tag, src):
            soup = BeautifulSoup(str(tag))
            img = soup.find('img')
            self.assertEqual(src, img['src'])

        tag = img_tag(None)
        has_src(tag, '/zcomix/static/images/portrait_placeholder.png')

        tag = img_tag(db.creator.image, size='original')
        has_src(tag, '/zcomix/images/download?size=original')

        tag = img_tag(db.creator.image, size='thumb')
        has_src(tag, '/zcomix/images/download?size=thumb')

        tag = img_tag(db.creator.image, size='_fake_')
        has_src(tag, '/zcomix/images/download?size=original')


def setUpModule():
    """Set up web2py environment."""
    # C0103: *Invalid name "%%s" (should match %%s)*
    # pylint: disable=C0103
    LocalTestCase.set_env(globals())


if __name__ == '__main__':
    unittest.main()
