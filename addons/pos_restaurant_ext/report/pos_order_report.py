# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import tools
from openerp.osv import fields, osv

_logger = logging.getLogger(__name__)


class POSOrderReport(osv.osv):
    _inherit = "report.pos.order"

    _columns = {
        'waiter_id': fields.many2one('pos.waiter', 'Waiter', readonly=True),
        'table_id': fields.many2one('restaurant.table', 'Table', readonly=True),
    }

    def _select(self):
        select_str = super(POSOrderReport, self)._select()
        select_str += """,
            s.waiter_id as waiter_id,
            s.table_id as table_id
        """
        return select_str

    def _group_by(self):
        group_by_str = super(POSOrderReport, self)._group_by()
        group_by_str += """,
            s.waiter_id,
            s.table_id
        """
        return group_by_str
