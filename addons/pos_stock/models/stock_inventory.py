#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _


_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    include_all_products = fields.Boolean(string='Include all products', default=False)
    categ_id = fields.Many2one('product.category', string='Product Category')

    def prepare_inventory(self, cr, uid, ids, context=None):
        inventory_line_obj = self.pool.get('stock.inventory.line')
        product_obj = self.pool.get('product.product')
        for inventory in self.browse(cr, uid, ids, context=context):
            line_ids = [line.id for line in inventory.line_ids]
            if not line_ids and inventory.filter == 'partial' and inventory.categ_id.id:
                vals = self._get_inventory_lines(cr, uid, inventory, context=context)
                for product_line in vals:
                    product = product_obj.browse(cr, uid, product_line['product_id'], context=context)
                    if product.categ_id.id == inventory.categ_id.id:
                        inventory_line_obj.create(cr, uid, product_line, context=context)

        return super(StockInventory, self).prepare_inventory(cr, uid, ids, context=context)

    def _get_inventory_lines(self, cr, uid, inventory, context=None):
        vals = super(StockInventory, self)._get_inventory_lines(cr, uid, inventory, context=context)
        if inventory.filter == 'none' and inventory.include_all_products:
            products_ids = [x['product_id'] for x in vals]
            product_obj = self.pool.get('product.product')
            add_products = product_obj.search(cr, uid, [('type', '=', 'product'), ('id', 'not in', products_ids)],
                                              context=context)
            for product in product_obj.browse(cr, uid, add_products, context=context):
                vals.append({
                    'inventory_id': inventory.id,
                    'location_id': inventory.location_id.id,
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'theoretical_qty': 0,
                    'product_qty': 0,
                })
        return vals
