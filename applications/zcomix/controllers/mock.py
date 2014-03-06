# -*- coding: utf-8 -*-
""" Search controller."""
import random
import re
from PIL import Image
from gluon.storage import Storage
from applications.zcomix.modules.search import Search
from applications.zcomix.modules.stickon.sqlhtml import LocalSQLFORM


def area_grid():
    """Front grid using area algorithm."""
    book = db(db.book).select(db.book.ALL, orderby=db.book.id).first()
    creator = db(db.creator.id == book.creator_id).select(db.creator.ALL).first()

    grid = Storage()
    grid.rows = []

    image_dir = os.path.join(request.folder, 'static', 'images', 'samples')
    images = sorted(os.listdir(image_dir))

    if request.vars.random:
        random.shuffle(images)

    try:
        ideal = int(request.vars.ideal) or 0
    except (TypeError, ValueError):
        ideal = 0

    ideal_area = 170 * ideal

    for image_name in images:
        dimensions = (0, 0)
        image_fullname = os.path.join(image_dir, image_name)
        with open(image_fullname, 'rb') as f:
            im = Image.open(f)
            dimensions = im.size
        w, h = dimensions
        if ideal_area:
            area = w * h
            if area > ideal_area:
                w = w * ideal_area / float(area)
                h = h * ideal_area / float(area)
        grid.rows.append(Storage(
            book=book,
            creator=creator,
            image_name=image_name,
            width=w,
            height=h,
        ))

    orderby_field = Search.order_fields['views']
    return dict(grid=grid, orderby_field=orderby_field, paginator=None)

def boot_thumbnail_grid():
    """Front grid using bootstrap thumbnails li
        http://getbootstrap.com/2.3.2/components.html#thumbnails
    """
    book = db(db.book).select(db.book.ALL, orderby=db.book.id).first()
    creator = db(db.creator.id == book.creator_id).select(db.creator.ALL).first()

    grid = Storage()
    grid.rows = []

    shrink_threshold = 120                  # pixels (max size is 170px)
    shrink_multiplier = 0.80

    image_dir = os.path.join(request.folder, 'static', 'images', 'samples')
    images = sorted(os.listdir(image_dir))
    if request.vars.random:
        random.shuffle(images)

    for image_name in images:
        dimensions = (0, 0)
        image_fullname = os.path.join(image_dir, image_name)
        with open(image_fullname, 'rb') as f:
            im = Image.open(f)
            dimensions = im.size

        w, h = dimensions

        shrink = True if h > shrink_threshold and w > shrink_threshold \
            else False
        if shrink:
            h = shrink_multiplier * h
            w = shrink_multiplier * w

        grid.rows.append(Storage(
            book=book,
            creator=creator,
            image_name=image_name,
            width=w,
            height=h,
        ))

    orderby_field = Search.order_fields['views']
    return dict(grid=grid, orderby_field=orderby_field, paginator=None)


def ratio_grid():
    """Front grid using ratio algorithm."""
    book = db(db.book).select(db.book.ALL, orderby=db.book.id).first()
    creator = db(db.creator.id == book.creator_id).select(db.creator.ALL).first()

    grid = Storage()
    grid.rows = []

    shrink_threshold = 120                  # pixels (max size is 170px)
    shrink_multiplier = 0.80

    image_dir = os.path.join(request.folder, 'static', 'images', 'samples')
    images = sorted(os.listdir(image_dir))
    if request.vars.random:
        random.shuffle(images)

    for image_name in images:
        dimensions = (0, 0)
        image_fullname = os.path.join(image_dir, image_name)
        with open(image_fullname, 'rb') as f:
            im = Image.open(f)
            dimensions = im.size

        w, h = dimensions

        shrink = True if h > shrink_threshold and w > shrink_threshold \
            else False
        if shrink:
            h = shrink_multiplier * h
            w = shrink_multiplier * w

        grid.rows.append(Storage(
            book=book,
            creator=creator,
            image_name=image_name,
            width=w,
            height=h,
        ))

    orderby_field = Search.order_fields['views']
    return dict(grid=grid, orderby_field=orderby_field, paginator=None)


def front_grid():
    """Mock of front page grid.

    request.vars.random: randomize order of images.
    """
    book = db(db.book).select(db.book.ALL, orderby=db.book.id).first()
    creator = db(db.creator.id == book.creator_id).select(db.creator.ALL).first()

    grid = Storage()
    grid.rows = []

    image_dir = os.path.join(request.folder, 'static', 'images', 'samples')
    images = sorted(os.listdir(image_dir))
    if request.vars.random:
        random.shuffle(images)
    for image_name in images:
        grid.rows.append(Storage(
            book=book,
            creator=creator,
            image_name=image_name,
        ))

    orderby_field = Search.order_fields['views']
    return dict(grid=grid, orderby_field=orderby_field, paginator=None)


def index():
    """Default controller."""
    return dict()
