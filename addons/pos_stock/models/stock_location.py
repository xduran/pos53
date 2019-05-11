#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _


_logger = logging.getLogger(__name__)


class StockLocation(models.Model):
    _inherit = 'stock.location'
    _order = 'sequence asc'

    sequence = fields.Integer(string='Sequence')
    quant_ids = fields.One2many('stock.quant', 'location_id', string='Current Stock',
                                help='The products storage in this location')
    inventory_value = fields.Float(string="Inventory Value", compute='_calc_inventory_value')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    picking_in_type_default = fields.Many2one('stock.picking.type', string='Default Picking In Type')
    picking_scrap_type_default = fields.Many2one('stock.picking.type', string='Default Scrap Picking Type')
    picking_expense_type_default = fields.Many2one('stock.picking.type', string='Default Expense Picking Type')
    picking_cost_type_default = fields.Many2one('stock.picking.type', string='Default Cost Picking Type')
    production_location = fields.Boolean('Is a Production Location?')

    @api.model
    def _initial_data(self):
        stock = self.env.ref('stock.stock_location_stock')
        poss = self.env.ref('pos_stock.stock_location_pos')
        poss.location_id = stock.location_id
        return True

    @api.multi
    def _calc_inventory_value(self):
        for location in self:
            if location.usage == 'internal':
                location_value = sum(location.quant_ids.mapped('inventory_value'))
                location.inventory_value = location_value

    def _get_action(self, cr, uid, ids, action, context=None):
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.xmlid_to_res_id(cr, uid, action, raise_if_not_found=True)
        result = act_obj.read(cr, uid, [result], context=context)[0]
        result['context'] = context
        return result

    def get_action_scrap_products(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if ids:
            location = self.browse(cr, uid, ids[0], context=context)
            context.update({
                'search_default_picking_type_id': [location.picking_scrap_type_default.id],
                'default_picking_type_id': location.picking_scrap_type_default.id,
                'default_location_id': location.id,
            })
        return self._get_action(cr, uid, ids, 'pos_stock.action_picking_form', context=context)

    def get_action_expense_products(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if ids:
            location = self.browse(cr, uid, ids[0], context=context)
            context.update({
                'search_default_picking_type_id': [location.picking_expense_type_default.id],
                'default_picking_type_id': location.picking_expense_type_default.id,
                'default_location_id': location.id,
            })
        return self._get_action(cr, uid, ids, 'pos_stock.action_picking_form', context=context)

    def get_action_cost_products(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if ids:
            location = self.browse(cr, uid, ids[0], context=context)
            context.update({
                'search_default_picking_type_id': [location.picking_cost_type_default.id],
                'default_picking_type_id': location.picking_cost_type_default.id,
                'default_location_id': location.id,
            })
        return self._get_action(cr, uid, ids, 'pos_stock.action_picking_form', context=context)

    def get_action_manufacture(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if ids:
            location = self.browse(cr, uid, ids[0], context=context)
            context.update({
                'default_location_src_id': location.id,
                'default_location_dest_id': location.id,
            })
        return self._get_action(cr, uid, ids, 'pos_stock.action_mrp_production', context=context)

    def get_action_transfer_products(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        if ids:
            location = self.browse(cr, uid, ids[0], context=context)
            context.update({
                'search_default_picking_type_id': [location.picking_in_type_default.id],
                'default_picking_type_id': location.picking_in_type_default.id,
            })
        return self._get_action(cr, uid, ids, 'pos_stock.action_picking_form', context=context)

    @api.multi
    def get_real_stock(self):
        location_ids = self.search([('id', 'child_of', self.id)]).ids
        domain = " location_id in %s "
        args = (tuple(location_ids),)

        self._cr.execute('''
           SELECT product_id, sum(qty) as product_qty
           FROM stock_quant WHERE''' + domain + '''
           GROUP BY product_id
        ''', args)
        vals = {}
        for product_line in self._cr.dictfetchall():
            if product_line['product_id']:
                vals[product_line['product_id']] = product_line['product_qty']

        return vals

    @api.multi
    def print_real_stock(self):
        # return self.env['report'].get_action(self, 'pos_stock.report_location_real_stock')
        return {
            'name': _('IPV to Print'),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'stock.ipv',
            'context': dict(
                self.env.context,
                default_location_id=self.id
            ),
        }