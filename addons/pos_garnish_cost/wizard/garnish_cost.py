#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _


_logger = logging.getLogger(__name__)


class GarnishCost(models.TransientModel):
    _name = 'garnish.cost.analysis'

    product_id = fields.Many2one('product.template', required=True)
    base_cost = fields.Float(related='product_id.standard_price', string='Fixed Cost', readonly=True)
    subtotal_cost = fields.Float(string='Subtotal', readonly=True, compute='_compute_fields', digits=(12, 6))
    total_cost = fields.Float(string='Total Cost', readonly=True, compute='_compute_fields', digits=(12, 6))
    line_ids = fields.One2many('garnish.cost.analysis.line', 'analysis_id')

    @api.multi
    @api.depends('product_id', 'base_cost', 'base_cost', 'line_ids.garnish_id')
    def _compute_fields(self):
        for item in self:
            item.subtotal_cost = sum(item.line_ids.mapped('cost'))
            item.total_cost = item.subtotal_cost + item.base_cost

    @api.multi
    def print_report(self):
        pass


class GarnishCostLine(models.TransientModel):
    _name = 'garnish.cost.analysis.line'

    analysis_id = fields.Many2one('garnish.cost.analysis', required=True)
    product_id = fields.Many2one('product.template')
    garnish_id = fields.Many2one('product.garnish', string='Product', required=True)
    category = fields.Many2one(related='garnish_id.category', readonly=True)
    sale_price = fields.Float(related='garnish_id.sale_price', readonly=True)
    cost = fields.Float(related='garnish_id.cost', readonly=True)

