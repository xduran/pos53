# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import tools
from openerp.osv import fields, osv

_logger = logging.getLogger(__name__)


class POSOrderReport(osv.osv):
    _name = "report.cash"
    _auto = False

    _columns = {
        'nbr': fields.integer('# of Lines', readonly=True),
        'date': fields.date('Date', readonly=True),
        'amount': fields.float('Amount', readonly=True),
        'pos_session_id': fields.many2one('pos.session', string="Session", readonly=True),
        'reason_id': fields.many2one('cash.box.reason', 'Reason', readonly=True),
        'reason_category_id': fields.many2one('cash.box.reason.category', 'Category', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
    }

    def _select(self):
        select_str = """
            min(l.id) as id,
            count(*) as nbr,
            l.date as date,
            sum(l.amount) as amount,
            l.company_id as company_id,
            l.pos_session_id as pos_session_id,
            l.reason_id as reason_id,
            l.reason_category_id as reason_category_id
        """
        return select_str

    def _from(self):
        from_str = """
            account_bank_statement_line as l
            left join account_journal j on (j.id=l.journal_id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            l.date,
            l.company_id,
            l.pos_session_id,
            l.reason_id,
            l.reason_category_id,
            j.type
        """
        return group_by_str

    def _having(self):
        having_str = """
            j.type = 'cash' and l.pos_session_id > 0
        """
        return having_str

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT %s
            FROM %s
            GROUP BY %s
            HAVING %s
            )""" % (self._table, self._select(), self._from(), self._group_by(), self._having()))
