# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

from openerp.osv import osv
from openerp.report import report_sxw


class RealStock(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(RealStock, self).__init__(cr, uid, name, context=context)
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        company_id = user.company_id
        self.localcontext.update({
            'company': company_id or False,
            'lines': self._get_lines,
        })

    def _get_lines(self):
        return self.pool.get('stock.ipv').browse(self.cr, self.uid, self.ids)[0].get_report_lines()


class ReportLocationRealStock(osv.AbstractModel):
    _name = 'report.pos_stock.report_location_real_stock'
    _inherit = 'report.abstract_report'
    _template = 'pos_stock.report_location_real_stock'
    _wrapped_report_class = RealStock
