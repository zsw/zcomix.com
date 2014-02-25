#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Test suite for zcomix/modules/utils.py

"""
import unittest
from BeautifulSoup import BeautifulSoup
from gluon import *
from applications.zcomix.modules.utils import \
    ItemDescription, \
    reorder
from applications.zcomix.modules.test_runner import LocalTestCase

# C0111: Missing docstring
# R0904: Too many public methods
# pylint: disable=C0111,R0904


class TestItemDescription(LocalTestCase):

    _description = '123456789 123456789 '

    def test____init__(self):
        item = ItemDescription(self._description)
        self.assertTrue(item)
        self.assertEqual(item.description, self._description)
        self.assertEqual(item.truncate_length, 200)

    def test__as_html(self):
        item = ItemDescription(None)
        self.assertEqual(
            str(item.as_html()),
            '<div></div>'
        )

        item = ItemDescription('')
        self.assertEqual(
            str(item.as_html()),
            '<div></div>'
        )

        # Test short item
        item = ItemDescription('123456789')
        self.assertEqual(
            str(item.as_html()),
            '<div>123456789</div>'
        )

        # Test long item, break on space
        item = ItemDescription(self._description)
        item.truncate_length = 10
        self.assertEqual(
            str(item.as_html()),
            '<div><div class="short_description">123456789 ... <a class="desc_more_link" data-w2p_disable_with="default" href="#">more</a></div><div class="full_description hidden">123456789 123456789 </div></div>'
        )

        # Test long item, break on word
        item = ItemDescription(self._description)
        item.truncate_length = 15
        self.assertEqual(
            str(item.as_html()),
            '<div><div class="short_description">123456789 ... <a class="desc_more_link" data-w2p_disable_with="default" href="#">more</a></div><div class="full_description hidden">123456789 123456789 </div></div>'
        )

        # Test attributes
        item = ItemDescription('123456789')
        self.assertEqual(
            str(item.as_html(**dict(_id='my_id'))),
            '<div id="my_id">123456789</div>'
        )


class TestFunctions(LocalTestCase):

    def test__reorder(self):

        db.define_table(
            'test__reorder',
            Field('name'),
            Field('order_no', 'integer'),
            migrate=True,
        )

        db.test__reorder.truncate()

        fields = ['a', 'b', 'c']
        by_name = {}
        for f in fields:
            record_id = db.test__reorder.insert(
                name=f,
                order_no=0,
            )
            db.commit()
            by_name[f] = record_id

        def reset():
            record_ids = [
                by_name['a'],
                by_name['b'],
                by_name['c'],
            ]
            reorder(db.test__reorder.order_no, record_ids=record_ids)

        def ordered_values(field='name'):
            """Get the field values in order."""
            values = db().select(
                db.test__reorder[field],
                orderby=[db.test__reorder.order_no, db.test__reorder.id],
            )
            return [x[field] for x in values]

        reorder(db.test__reorder.order_no)
        self.assertEqual(ordered_values(), ['a', 'b', 'c'])

        # Test record_ids param
        reset()
        record_ids = [
            by_name['b'],
            by_name['c'],
            by_name['a'],
        ]
        reorder(db.test__reorder.order_no, record_ids=record_ids)
        self.assertEqual(ordered_values(), ['b', 'c', 'a'])

        # Test query param
        reset()
        query = (db.test__reorder.id > 0)
        reorder(db.test__reorder.order_no, query=query)
        self.assertEqual(ordered_values(), ['a', 'b', 'c'])

        # Test start param
        reset()
        reorder(db.test__reorder.order_no, start=100)
        self.assertEqual(ordered_values(), ['a', 'b', 'c'])
        self.assertEqual(ordered_values(field='order_no'), [100, 101, 102])

        # Add record to table
        reset()
        db.test__reorder.insert(
            name='d',
            order_no=9999,
        )
        db.commit()
        reorder(db.test__reorder.order_no)
        self.assertEqual(ordered_values(), ['a', 'b', 'c', 'd'])

        # Delete record from table
        reset()
        db(db.test__reorder.name == 'b').delete()
        db.commit()
        reorder(db.test__reorder.order_no)
        self.assertEqual(ordered_values(), ['a', 'c', 'd'])
        self.assertEqual(ordered_values(field='order_no'), [1, 2, 3])


def setUpModule():
    """Set up web2py environment."""
    # C0103: *Invalid name "%%s" (should match %%s)*
    # pylint: disable=C0103
    LocalTestCase.set_env(globals())


if __name__ == '__main__':
    unittest.main()
