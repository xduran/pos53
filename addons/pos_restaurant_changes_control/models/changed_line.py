# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
#  -*- coding: utf-8 -*-

import logging
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


_logger = logging.getLogger(__name__)


class ChangedLine(models.Model):
    _name = 'pos.changed.line'
    _order = "create_date desc"

    create_date = fields.Datetime(string="Creation Date", readonly=True, select=True)
    session_id = fields.Many2one('pos.session', string='Session', required=True, select=1, readonly=True)
    table_id = fields.Many2one('restaurant.table', readonly=True, string='Table')
    product_id = fields.Many2one('product.product', string='Product', readonly=True, required=True)
    printed_quantity = fields.Float(string='Printed Quantity', readonly=True, digits=0)
    final_quantity = fields.Float(string='Final Quantity', readonly=True, digits=0)
    printed_price_unit = fields.Float(string='Printed Unit Price', readonly=True, digits=0)
    final_price_unit = fields.Float(string='Final Unit Price', readonly=True, digits=0)
    printed_discount = fields.Float(string='Printed Discount (%)', readonly=True, digits=0)
    final_discount = fields.Float(string='Final Discount (%)', readonly=True, digits=0)
    pos_categ_id = fields.Many2one(related='product_id.pos_categ_id')
    config_id = fields.Many2one(related='session_id.config_id')
    user_id = fields.Many2one(related='session_id.user_id')
    order_id = fields.Many2one('pos.order', string='Order', select=1, readonly=True)

    def create_from_ui(self, cr, uid, lines, context=None):
        """ create a changed line records from the point of sale ui."""
        result = []
        for line in lines:
            result.append(self.create(cr, uid, line, context=context))
        return result


class POSOrder(models.Model):
    _inherit = "pos.order"

    printed_times = fields.Integer(string='Printed Times', readonly=True)
    changed_lines = fields.One2many('pos.changed.line', 'order_id', string='Changed Lines',
                                    help="Changes made in order after printing it.")

    def _order_fields(self, cr, uid, ui_order, context=None):
        result = super(POSOrder, self)._order_fields(cr, uid, ui_order, context=context)
        result['printed_times'] = ui_order['printed_times']
        changed_lines = ui_order['changed_lines']
        result['changed_lines'] = [[0, 0, x] for x in changed_lines]
        return result


class POSConfig(models.Model):
    _inherit = 'pos.config'

    iface_changes_control = fields.Boolean(string="Changes Control", default=True,
                                           help="Allows to keep track of changes in order lines.")

