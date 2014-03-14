#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

stickon/sqlhtml.py

Classes extending functionality of gluon/sqlhtml.py particular to the zcomix
application.

"""
import logging
from gluon import *
from gluon.sqlhtml import FormWidget

# E1101: *%s %r has no %r member*
# pylint: disable=E1101

LOG = logging.getLogger('app')


class InputWidget(FormWidget):
    """Custom input widget."""

    def __init__(self, attributes=None, class_extra=''):
        """Constructor.

        Args:
            attributes: dict, dictionary of custom attributes.
            class_extra: string, value appended to _class value.
        """
        # W0221: Arguments number differs from overridden method
        # W0231: __init__ method from base class FormWidget is not called
        # pylint: disable=W0221,W0231

        self.attributes = attributes if attributes else {}
        self.class_extra = class_extra

    def widget(self, field, value, **attributes):
        """Generate INPUT tag for custom widget.

        See gluon.sqlhtml FormWidget
        """
        # W0221: Arguments number differs from overridden method
        # pylint: disable=W0221

        new_attributes = dict(
            _type='text',
            _value=(value != None and str(value)) or '',
            )
        new_attributes.update(self.attributes)
        attr = self._attributes(field, new_attributes, **attributes)
        if self.class_extra:
            attr['_class'] = ' '.join([attr['_class'], self.class_extra])
        return INPUT(**attr)


class LocalSQLFORM(SQLFORM):
    """Class representing a SQLFORM with preset defaults and customizations.
    """
    grid_defaults = {
            'paginate': 35,
            'ui': dict(widget='grid_widget',
                  header='grid_header',
                  content='',
                  default='grid_default',
                  cornerall='',
                  cornertop='',
                  cornerbottom='',
                  button='button btn btn-default',
                  buttontext='buttontext button',
                  buttonadd='glyphicon glyphicon-plus',
                  buttonback='glyphicon glyphicon-arrow-left',
                  buttonexport='glyphicon glyphicon-download',
                  buttondelete='glyphicon glyphicon-trash',
                  buttonedit='glyphicon glyphicon-pencil',
                  buttontable='glyphicon glyphicon-arrow-right',
                  buttonview='glyphicon glyphicon-zoom-in',
                  ),
            }

    @staticmethod
    def grid(*args, **kwargs):
        """Override grid method and set ui defaults."""
        for k, v in LocalSQLFORM.grid_defaults.items():
            if k not in kwargs:
                kwargs[k] = v
        return SQLFORM.grid(*args, **kwargs)
