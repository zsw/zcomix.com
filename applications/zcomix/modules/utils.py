#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Utilty classes and functions.
"""
from gluon import *


class ItemDescription(object):
    """Class representing an item description field.

    A description of an item is usually a blob of text. This class provides
    methods to format the description.
    """
    # If description is longer than this, the description is truncated with a
    # '... more' link.
    truncate_length = 200

    def __init__(self, description):
        """Constructor

        Args:
            description: string, the full-length item description
        """
        self.description = description

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
                'more',
                _href='#',
                _class='desc_more_link',
            )

            short_div = DIV(
                short_description,
                ' ... ',
                anchor,
                _class='short_description',
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
