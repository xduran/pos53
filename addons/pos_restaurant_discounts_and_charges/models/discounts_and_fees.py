#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


class POSConfig(models.Model):
    _inherit = 'pos.config'

    iface_display_taxes = fields.Boolean(string='Display Taxes', help='Display taxes in orders')
    iface_allow_tip = fields.Boolean(string='Tip',
                                     help="Allow the cashier to register customer's tips")
    iface_global_discount = fields.Boolean(string='Order Discounts',
                                           help='Allow the cashier to give discounts on the whole order')
    iface_service_fee = fields.Boolean(string='Service Fee',
                                       help='Allow the cashier to charge the customer for the service received')
    service_pc = fields.Float(string='Service Percentage', default=10, help='The default service percentage')
    service_product_id = fields.Many2one('product.product', string='Service Product',
                                         help='The product used to represent the service fees')
    discount_product_id = fields.Many2one('product.product', string='Discount Product',
                                          help='The product used to represent the discounts')


class POSOrder(models.Model):
    _inherit = "pos.order"

    discount_pc = fields.Float(string='Discount Percentage', readonly=True, states={'draft': [('readonly', False)]},
                               help='The order discount percentage')
    service_pc = fields.Float(string='Service Percentage', readonly=True, states={'draft': [('readonly', False)]},
                              help='The order service percentage')
    total_discount = fields.Float(string='Total Discount', compute='_fields_compute', readonly=True, store=True)
    total_sale = fields.Float(string='Net Sale', compute='_fields_compute', readonly=True, store=True,
                              help='The net income related to the sale')
    subtotal = fields.Float(string='Subtotal', compute='_fields_compute', readonly=True, store=True)
    service_fee = fields.Float(string='Service Fee', compute='_fields_compute', readonly=True, store=True)
    tip = fields.Float(string='Tip', compute='_fields_compute', readonly=True, store=True)

    iface_allow_tip = fields.Boolean(related='session_id.config_id.iface_allow_tip')
    iface_global_discount = fields.Boolean(related='session_id.config_id.iface_global_discount')
    iface_service_fee = fields.Boolean(related='session_id.config_id.iface_service_fee')

    @api.multi
    @api.depends('lines')
    def _fields_compute(self):
        for order in self:
            tip = 0
            tip_id = False
            service = 0
            service_id = False
            discount = 0
            discount_id = False
            subtotal = 0
            if order.config_id.iface_allow_tip and order.config_id.tip_product_id:
                tip_id = order.config_id.tip_product_id
            if order.config_id.iface_service_fee and order.config_id.service_product_id:
                service_id = order.config_id.service_product_id
            if order.config_id.iface_global_discount and order.config_id.discount_product_id:
                discount_id = order.config_id.discount_product_id
            for line in order.lines:
                if tip_id and line.product_id == tip_id:
                    tip = line.base_price
                elif discount_id and line.product_id == discount_id:
                    discount = line.base_price
                elif service_id and line.product_id == service_id:
                    service = line.base_price
                else:
                    subtotal += line.base_price
            order.tip = tip
            order.service_fee = service
            order.subtotal = subtotal
            order.total_discount = discount
            order.total_sale = subtotal + discount

    def _order_fields(self, cr, uid, ui_order, context=None):
        session_obj = self.pool.get('pos.session')
        session_id = ui_order['pos_session_id']
        if ui_order.get('tip', False):
            tip_product = session_obj.browse(cr, uid, session_id, context=context).config_id.tip_product_id
            product_ids = [x[2]['product_id'] for x in ui_order['lines']]
            if tip_product.id not in product_ids:
                tip_amount = ui_order['tip']
                ui_order['lines'].append([0, 0, {
                    'product_id': tip_product.id,
                    'qty': 1,
                    'price_unit': tip_amount,
                }])
        if ui_order.get('discount_pc', False):
            discount_product = session_obj.browse(cr, uid, session_id, context=context).config_id.discount_product_id
            discount_amount = ui_order['discount_amount']
            ui_order['lines'].append([0, 0, {
                'product_id': discount_product.id,
                'qty': 1,
                'price_unit': discount_amount * -1,
            }])
        if ui_order.get('service_pc', False):
            service_product = session_obj.browse(cr, uid, session_id, context=context).config_id.service_product_id
            service_amount = ui_order['service_amount']
            ui_order['lines'].append([0, 0, {
                'product_id': service_product.id,
                'qty': 1,
                'price_unit': service_amount,
            }])

        order_fields = super(POSOrder, self)._order_fields(cr, uid, ui_order, context=context)
        order_fields['discount_pc'] = ui_order.get('discount_pc', 0)
        order_fields['service_pc'] = ui_order.get('service_pc', 0)
        return order_fields


class POSOrderLIne(models.Model):
    _inherit = "pos.order.line"

    base_price = fields.Float(string='Base Price', compute='_compute_base_price', readonly=True,
                              help='The line price before discount', store=True)

    @api.multi
    @api.depends('price_unit', 'qty')
    def _compute_base_price(self):
        for order_line in self:
            order_line.base_price = order_line.price_unit * order_line.qty


class POSSession(models.Model):
    _inherit = 'pos.session'

    total_sale = fields.Float(string='Net Sale', compute='_compute_totals', readonly=True,
                              help='The net income related to the sale', store=True)
    bank_sale = fields.Float(string='Bank', compute='_compute_totals', readonly=True, store=True)
    cash_sale = fields.Float(string='Cash', compute='_compute_totals', readonly=True, store=True)
    total_discount = fields.Float(string='Total Discount', compute='_compute_totals', readonly=True,
                                  help='The total discounted in sales', store=True)
    service_fee = fields.Float(string='Service Fee', compute='_compute_totals', readonly=True,
                               help='The total service fee applied to customers', store=True)
    tip = fields.Float(string='Tip', compute='_compute_totals', readonly=True,
                       help='The total amount received as tip', store=True)
    iface_allow_tip = fields.Boolean(related='config_id.iface_allow_tip')
    iface_global_discount = fields.Boolean(related='config_id.iface_global_discount')
    iface_service_fee = fields.Boolean(related='config_id.iface_service_fee')

    @api.multi
    @api.depends('order_ids', 'statement_ids', 'statement_ids.balance_end_real')
    def _compute_totals(self):
        for session in self:
            sales = 0
            service = 0
            discount = 0
            tip = 0
            bank = 0
            for order in session.order_ids:
                sales += order.total_sale
                service += order.service_fee
                discount += order.total_discount
                tip += order.tip
            for stmt in session.statement_ids:
                if stmt.journal_type == 'bank':
                    bank += stmt.balance_end_real
            session.bank_sale = bank
            session.cash_sale = sales - bank
            session.total_sale = sales
            session.total_discount = discount
            session.service_fee = service
            session.tip = tip


class POSConfig(models.Model):
    _inherit = 'pos.config'

    total_sale = fields.Float(string="Net Sale", related='active_session.total_sale')
    total_discount = fields.Float(string="Total Discount", related='active_session.total_discount')
    service_fee = fields.Float(string="Service Fee", related='active_session.service_fee')
    tip = fields.Float(string="Tip", related='active_session.tip')


class Partner(models.Model):
    _inherit = 'res.partner'

    pos_discount = fields.Float(string='Discount', default=0,
                                help='The default discount percentage to apply in orders of this customer.')
