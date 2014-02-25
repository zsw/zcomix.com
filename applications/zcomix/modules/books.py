#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Book classes and functions.
"""
import os
import stat
from gluon import *
from gluon.contrib.simplejson import dumps
from applications.zcomix.modules.images import img_tag


def book_pages_as_json(db, book_id, book_page_ids=None):
    """Return the book pages formated as json suitable for jquery-file-upload.

    Args:
        db: gluon.dal.DAL instance
        book_id: integer, the id of the book record
        book_page_ids: list of ids, integers of book_page records. By default
            all pages of book are returned. With this option only pages with
            ids in this list are returned.

    Returns:
        string, json formatted book_page data
            {'files': [
                {
                    ... see book_page_for_json ...
                },
            ]
            }

    """
    pages = []
    query = (db.book_page.book_id == book_id)
    if book_page_ids:
        query = query & (db.book_page.id.belongs(book_page_ids))
    records = db(query).select(db.book_page.id, orderby=db.book_page.page_no)
    for record in records:
        pages.append(book_page_for_json(db, record.id))
    return dumps(dict(files=pages))


def book_page_for_json(db, book_page_id):
    """Return the book_page formated as json suitable for jquery-file-upload.

    Args:
        db: gluon.dal.DAL instance
        book_page_id: integer, the id of the book_page record

    Returns:
        dict, containing book_page data suitable for jquery-file-upload
                {
                    "name": "picture1.jpg",
                    "size": 902604,
                    "url": "http:\/\/example.org\/files\/picture1.jpg",
                    "thumbnailUrl": "http:\/\/example.org\/files\/thumbnail\/picture1.jpg",
                    "deleteUrl": "http:\/\/example.org\/files\/picture1.jpg",
                    "deleteType": "DELETE"
                },
    """
    book_page = db(db.book_page.id == book_page_id).select(db.book_page.ALL).first()
    if not book_page:
        return

    filename, original_fullname = db.book_page.image.retrieve(
        book_page.image,
        nameonly=True,
    )

    try:
        size = os.stat(original_fullname).st_size
    except (KeyError, OSError):
        size = 0

    url = URL(
        c='images',
        f='download',
        args=book_page.image,
    )

    thumb = URL(
        c='images',
        f='download',
        args=book_page.image,
        vars={'size': 'thumb'},
    )

    delete_url = URL(
        c='profile',
        f='book_pages_handler',
        args=book_page.book_id,
        vars={'book_page_id': book_page.id},
    )

    return dict(
        book_id=book_page.book_id,
        book_page_id=book_page.id,
        name=filename,
        size=size,
        url=url,
        thumbnailUrl=thumb,
        deleteUrl=delete_url,
        deleteType='DELETE',
    )


def cover_image(db, book_id, size='original'):
    """Return html code suitable for the cover image.

    Args:
        db: gluon.dal.DAL instance
        book_id: integer, the id of the book
        size: string, the size of the image. One of Resizer.sizes.keys()
    """
    query = (db.book_page.book_id == book_id)
    first_page = db(query).select(
        db.book_page.image,
        orderby=db.book_page.page_no
    ).first()
    image = first_page.image if first_page else None
    return img_tag(image, size=size)


def read_link(db, book_entity, **attributes):
    """Return html code suitable for the cover image.

    Args:
        db: gluon.dal.DAL instance
        book_entity: Row instance or integer, if integer, this is the id of the
            book. The book record is read.
        attributes: dict of attributes for A()
    """
    empty = SPAN('')

    book = None
    if hasattr(book_entity, 'id'):
        book = book_entity
    else:
        # Assume book is an id
        book = db(db.book.id == book_entity).select().first()

    if not book:
        return empty

    kwargs = {}
    kwargs.update(attributes)

    if '_href' not in attributes:
        reader = book.reader or 'slider'
        url = URL(c='books', f=reader, args=book.id, extension=False)
        kwargs['_href'] = url
    return A('READ', **kwargs)
