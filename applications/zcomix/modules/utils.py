#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Utilty classes and functions.
"""
import collections
from gluon import *


class ItemDescription(object):
    """Class representing an item description field.

    A description of an item is usually a blob of text. This class provides
    methods to format the description.
    """

    def __init__(self, description, more_text='more', truncate_length=200):
        """Constructor

        Args:
            description: string, the full-length item description
            more_text: string, the text used for the 'more' link.
            truncate_length: integer, if description is longer than this,
                the description is truncated with a '... more' link.
        """
        self.description = description
        self.more_text = more_text
        self.truncate_length = truncate_length

    def as_html(self, **attributes):
        """Return the HTML representation of the description.

        Args:
            attributes: dict of attributes of container DIV
        """
        short_description = self.description
        if self.description and len(self.description) > self.truncate_length:
            try:
                sections = \
                    self.description[:self.truncate_length].rsplit(None, 1)
                short_description = sections[0]
            except (KeyError, TypeError):
                short_description = ''

        divs = []

        if short_description and short_description != self.description:
            anchor = A(
                self.more_text,
                _href='#',
                _class='desc_more_link',
            )

            short_div = DIV(
                short_description,
                ' ... ',
                anchor,
                _class='short_description',
                _title=self.description,
            )

            full_div = DIV(
                self.description,
                _class='full_description hidden',
            )

            divs = [short_div, full_div]
        else:
            divs = [self.description or '']

        kwargs = {}
        kwargs.update(attributes)

        return DIV(*divs, **kwargs)


def move_record(sequential_field, record_id, direction='up', query=None, start=1):
    """Move a record in the direction.

    Args:
        sequential_field: gluon.dal.Field instance
        record_id: integer, id of record to move.
        direction: string, 'up' or 'down'
        query: gluon.dal.Query, a query used to filter records updated.
            Only records returned by this query will be reordered.
                db(query).select()
            If None, all records of the table are reordered.
        start: integer, the sequential field value of the first record is set
            to this. Subsequent records have values incremented by 1.
    """
    db = sequential_field._db
    table = sequential_field.table

    record = db(table.id == record_id).select(table.ALL).first()
    if not record:
        # If the record doesn't exist, it can't be moved.
        return

    # Create a list of ids in order except for the one that is moved.
    filter_query = (table.id != record_id)
    if query:
        filter_query = filter_query & query
    rows = db(filter_query).select(table.id, orderby=sequential_field)
    record_ids = [x.id for x in rows]

    # Insert the moved record in it's new location.
    old_order_value = record[sequential_field.name]
    new_order_value = old_order_value + 1 if direction == 'down' \
        else old_order_value - 1
    if new_order_value < start:
        new_order_value = start
    record_ids.insert(new_order_value - 1, record.id)
    reorder(sequential_field, record_ids=record_ids, query=query, start=start)


def profile_wells(request):
    """Return data for wells on the profile page.

    Args:
        request: gluon.globals.Request instance

    Returns:
        dict of well data
    """
    # The keys of wells_data must match the profile controller names.
    # Wells are displayed in the order of wells_data.
    active_well = request.function

    wells_data = [
        # (key, {data})
        ('account', {'label': 'Account Profile'}),
        ('creator', {'label': 'Creator Profile'}),
        ('creator_links', {
            'label': 'Creator Links',
            'show_children': False,         # Children links in grid
        }),
        ('creator_link_edit', {
            'label': 'Creator Link Edit',
            'parent': 'creator_links',
        }),
        ('books', {
            'label': 'Books',
            'show_children': False,         # Children links in grid
        }),
        ('book_edit', {
            'label': 'Book Edit',
            'parent': 'books',
            'args': request.args,
        }),
        ('book_pages', {
            'label': 'Book Pages',
            'parent': 'book_edit',
            'args': request.args,
        }),
        ('book_links', {
            'label': 'Book Links',
            'parent': 'book_edit',
            'show_children': False,         # Children links in grid
            'args': request.args,
        }),
        ('book_link_edit', {
            'label': 'Book Link Edit',
            'parent': 'book_links',
            'args': request.args,
        }),
        ('book_release', {
            'label': 'Book Release',
            'parent': 'books',
            'args': request.args,
        }),
    ]
    wells = collections.OrderedDict(wells_data)

    # Calculate the children of each.
    for well in wells.keys():
        wells[well]['children'] = []

    for well in wells.keys():
        if 'parent' in wells[well] and wells[well]['parent'] in wells:
            wells[wells[well]['parent']]['children'].append(well)

    # Calculate the status, None=hide, 'link'= as link, 'text'= as text
    for well in wells.keys():
        wells[well]['status'] = None
        if 'show_children' not in wells[well]:
            wells[well]['show_children'] = True

    # Set all wells with no parents as shown
    for well in wells.keys():
        if 'parent' not in wells[well] or not wells[well]['parent']:
            wells[well]['status'] = 'link'

    if request.function in wells:
        # Show children of active well if applicable
        if wells[request.function]['children'] and wells[request.function]['show_children']:
            for w in wells[request.function]['children']:
                wells[w]['status'] = 'link'

        # Recursively show all parents of active well.
        current = request.function
        while current:
            wells[current]['status'] = 'link'
            if 'parent' in wells[current]:
                current = wells[current]['parent']
            else:
                current = None

        # Show the active link as text.
        wells[request.function]['status'] = 'text'

    return wells


def reorder(sequential_field, record_ids=None, query=None, start=1):
    """Reset a table's sequential field values.

    Args:
        sequential_field: gluon.dal.Field instance
        record_ids: list of integers, ids of records of the table in
            sequential order. If None, a list is created from the ids of the
            records of the table in order by sequential_field.
        query: gluon.dal.Query, a query used to filter records updated.
            Only records returned by this query will be reordered.
                db(query).select()
            If None, all records of the table are reordered.
            This is ignored if record_ids is provided.
        start: integer, the sequential field value of the first record is set
            to this. Subsequent records have values incremented by 1.
    """
    db = sequential_field._db
    table = sequential_field.table
    if not record_ids:
        if query is None:
            query = (table.id > 0)
        rows = db(query).select(
            table.id,
            orderby=[sequential_field, table.id]
        )
        record_ids = [x.id for x in rows]
    for count, record_id in enumerate(record_ids, start):
        update_query = (table.id == record_id) & \
            (sequential_field != count)       # Only update if value is changed
        db(update_query).update(**{sequential_field.name: count})
        db.commit()
