#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _


_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    move_value = fields.Float(compute='_compute_value', store=True)
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id')

    @api.multi
    @api.depends('quant_ids', 'quant_ids.inventory_value')
    def _compute_value(self):
        for move in self:
            move.move_value = sum(move.quant_ids.mapped('inventory_value'))

    def _store_average_cost_price(self, cr, uid, move, context=None):
        if any([q.qty <= 0 for q in move.quant_ids]) or move.product_qty == 0:
            return
        average_valuation_price = 0.0
        for q in move.quant_ids:
            average_valuation_price += q.qty * q.cost
        average_valuation_price = average_valuation_price / move.product_qty
        self.write(cr, uid, [move.id], {'price_unit': average_valuation_price}, context=context)