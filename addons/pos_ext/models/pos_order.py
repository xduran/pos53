# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
import pytz
import datetime
from openerp import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


_logger = logging.getLogger(__name__)

WEEK_DAYS = [
    ('1', 'Monday'),
    ('2', 'Tuesday'),
    ('3', 'Wednesday'),
    ('4', 'Thursday'),
    ('5', 'Friday'),
    ('6', 'Saturday'),
    ('7', 'Sunday')
]


class POSOrderLIne(models.Model):
    _inherit = "pos.order.line"

    cost_price = fields.Float(string='Cost Price', compute='_compute_cost_price', readonly=True, store=True)

    @api.multi
    @api.depends('product_id', 'qty')
    def _compute_cost_price(self):
        for order_line in self:
            order_line.cost_price = order_line.product_id.standard_price * order_line.qty


class POSOrder(models.Model):
    _inherit = "pos.order"

    date = fields.Date(string='Date', compute='_compute_date', store=True, readonly=True)
    week_day = fields.Selection(WEEK_DAYS, string='Weekday', compute='_compute_date', store=True, readonly=True)
    week = fields.Char(string='Week', compute='_compute_date', store=True, readonly=True)
    month_day = fields.Char(string='Month Day', compute='_compute_date', store=True, readonly=True)
    day_hour = fields.Char(string='Day Interval', compute='_compute_hour', store=True, readonly=True)
    hour = fields.Integer(string='Hour', compute='_compute_hour', store=True, readonly=True)
    picking_ids = fields.One2many('stock.picking', 'pos_order', string="Pickings")
    order_cost = fields.Float(string='Cost', compute='_compute_cost', store=True, readonly=True)

    @api.multi
    @api.depends('lines')
    def _compute_cost(self):
        for order in self:
            cost = 0
            for line in order.lines:
                cost += line.cost_price
            order.order_cost = cost

    @api.multi
    @api.depends('session_id')
    def _compute_date(self):
        for order in self:
            session_date = datetime.datetime.strptime(order.session_id.start_at, DATETIME_FORMAT)
            order.date = session_date.strftime('%Y-%m-%d')
            order.week_day = session_date.strftime('%u')
            order.week = session_date.strftime('%Y-%W')
            order.month_day = session_date.strftime('%e')

    @api.multi
    @api.depends('date_order')
    def _compute_hour(self):
        tz_name = self._context.get('tz') or self.env.user.tz
        for order in self:
            order_date = datetime.datetime.strptime(order.date_order, DATETIME_FORMAT)
            context_date = order_date
            if tz_name:
                try:
                    date_utc = pytz.timezone('UTC').localize(order_date, is_dst=False)  # UTC = no DST
                    context_date = date_utc.astimezone(pytz.timezone(tz_name))
                except Exception:
                    _logger.debug("failed to compute context/client-specific today date, using UTC value for `today`",
                                  exc_info=True)
            order.hour = int(context_date.strftime('%H%M'))
            order.day_hour = '%s - %s' % (context_date.strftime('%H'),
                                          (context_date + datetime.timedelta(hours=1)).strftime('%H'))

    def _get_product_quantities(self, cr, uid, ids, context=None):
        """this logic is separated from the create picking method to allow injection of other moves"""
        product_qtys = []
        for order in self.browse(cr, uid, ids, context=context):
            for line in order.lines:
                if line.product_id and line.product_id.type not in ['product', 'consu'] or line.qty == 0:
                    continue
                product_qtys.append({
                    'name': line.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                })
        return product_qtys

    def create_picking(self, cr, uid, ids, context=None):
        """Create a picking for each order and validate it."""
        picking_obj = self.pool.get('stock.picking')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        move_obj = self.pool.get('stock.move')

        for order in self.browse(cr, uid, ids, context=context):
            if all(t == 'service' for t in order.lines.mapped('product_id.type')):
                continue
            rules = dict([(x.area_id.id, x.location_id.id) for x in order.session_id.config_id.area_location_rules])
            addr = order.partner_id and partner_obj.address_get(cr, uid, [order.partner_id.id], ['delivery']) or {}
            picking_type = order.picking_type_id
            location_id = order.location_id.id
            if order.partner_id:
                destination_id = order.partner_id.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = self.pool['stock.warehouse']._get_partner_locations(cr, uid, [],
                                                                                                   context=context)
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id

            # All qties negative => Create negative
            if picking_type:
                sources_map = {}
                move_list = []
                pos_qty = all([x.qty >= 0 for x in order.lines])
                product_qtys = self._get_product_quantities(cr, uid, [order.id], context=context)
                for elem in product_qtys:
                    elem_picking_id = False
                    source_location_id = location_id
                    product = product_obj.browse(cr, uid, elem['product_id'], context=context)
                    if product.area_id and product.area_id.id in rules:
                        source_location_id = rules[product.area_id.id]
                    if source_location_id in sources_map:
                        elem_picking_id = sources_map[source_location_id]
                    else:
                        elem_picking_id = picking_obj.create(cr, uid, {
                            'origin': order.name,
                            'pos_order': order.id,
                            'partner_id': addr.get('delivery', False),
                            'date_done': order.date_order,
                            'picking_type_id': picking_type.id,
                            'company_id': order.company_id.id,
                            'move_type': 'direct',
                            'note': order.note or "",
                            'location_id': source_location_id if pos_qty else destination_id,
                            'location_dest_id': destination_id if pos_qty else source_location_id,
                        }, context=context)
                        sources_map[source_location_id] = elem_picking_id

                    elem.update({
                        'picking_id': elem_picking_id,
                        'picking_type_id': picking_type.id,
                        'state': 'draft',
                        'location_id': source_location_id if elem['product_uom_qty'] >= 0 else destination_id,
                        'location_dest_id': destination_id if elem['product_uom_qty'] >= 0 else source_location_id,
                    })

                    move_list.append(move_obj.create(cr, uid, elem, context=context))

                for key in sources_map:
                    picking_obj.action_confirm(cr, uid, [sources_map[key]], context=context)
                    picking_obj.force_assign(cr, uid, [sources_map[key]], context=context)
                    # Mark pack operations as done
                    pick = picking_obj.browse(cr, uid, sources_map[key], context=context)
                    for pack in pick.pack_operation_ids:
                        self.pool['stock.pack.operation'].write(cr, uid, [pack.id], {'qty_done': pack.product_qty},
                                                                context=context)
                    picking_obj.action_done(cr, uid, [sources_map[key]], context=context)

        return True


class StockPicking(models.Model):
    _inherit = "stock.picking"

    pos_order = fields.Many2one('pos.order', string="Pos Order")


class StockPicking(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(digits=(12, 6))
