# -*- coding: utf-8 -*-
"""Creator controller functions"""

from applications.zcomix.modules.links import CustomLinks
from applications.zcomix.modules.stickon.sqlhtml import LocalSQLFORM


def books():
    """Creator books report controller.
    request.args(0): integer, id of creator.
    """
    return dict()


def creator():
    """Creator page
    request.args(0): integer, id of creator.
    """
    if not request.args(0):
        redirect(URL(c='default', f='index'))

    creator_record = db(db.creator.id == request.args(0)).select(
        db.creator.ALL
    ).first()
    if not creator_record:
        redirect(URL(c='default', f='index'))

    return dict(
        creator=creator_record,
        links=CustomLinks(db.creator, creator_record.id).represent(),
    )


def index():
    """Creators CRUD grid."""
    # This is no longer used
    redirect(URL(c='default', f='index'))
