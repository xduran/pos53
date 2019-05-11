#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _


_logger = logging.getLogger(__name__)


class ProductIdealStock(models.Model):
    _name = 'product.ideal.stock'
    _description = 'The ideal stock for a product by location'

    location_id = fields.Many2one('stock.location', string='Location', required=True,
                                  domain=[('usage', '=', 'internal')])
    product_id = fields.Many2one('product.template', string='Product', required=True, domain=[('type', '=', 'product')])
    qty = fields.Float(string='Quantity', required=True, default=0.0)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', related='product_id.uom_id', readonly=True)
    uom_po_id = fields.Many2one('product.uom', string='Purchase Unit of Measure', related='product_id.uom_po_id',
                                readonly=True)

    @api.multi
    def get_stock_need(self):
        result = []
        uom_obj = self.env['product.uom']
        for pis in self:
            location = pis.location_id
            quants = location.quant_ids.filtered(lambda r: r.product_id.product_tmpl_id.id == pis.product_id.id)
            qty_available = sum([q.qty for q in quants])
            if qty_available < pis.qty:
                qty = int(uom_obj._compute_qty(pis.uom_id.id, pis.qty - qty_available, pis.uom_po_id.id))
                if qty > 0:
                    result.append((pis.product_id.name, qty, pis.uom_po_id.name))
        return result


class Product(models.Model):
    _inherit = 'product.template'

    ideal_stock_ids = fields.One2many('product.ideal.stock', 'product_id', string='Ideal Stock')
