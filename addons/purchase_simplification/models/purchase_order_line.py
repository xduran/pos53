#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _

_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.one
    def _set_price_unit(self):
        self.price_unit = self.price_subtotal / self.product_qty

    price_subtotal = fields.Monetary(inverse='_set_price_unit')
    price_unit = fields.Float(digits=(12, 6))
    partner_ref = fields.Char('Vendor Reference', copy=False)

    def fix_partner_ref(self, cr, uid, **args):
        lines_ids = self.search(cr, uid, [])
        lines = self.browse(cr, uid, lines_ids)
        for line in lines:
            self.write(cr, uid, line.id, {'partner_ref': line.order_id.partner_ref})
