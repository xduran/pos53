#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


_logger = logging.getLogger(__name__)


class IPV(models.Model):
    _name = 'stock.ipv'
    _order = 'date desc'
    _rec_name = 'date'

    @api.model
    def _get_default_compare_to(self):
        context = dict(self._context or {})
        location_id = context.get('default_location_id', False)
        if location_id:
            compare_to = self.search([('location_id', '=', location_id)])
            if len(compare_to):
                return compare_to[0].id
        return False

    date = fields.Datetime(string='Date', default=fields.Datetime.now, readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='State', default='draft')
    location_id = fields.Many2one('stock.location', string='Location', required=True, ondelete='cascade',
                                  states={'done': [('readonly', True)]})
    ipv_type = fields.Selection([('initial', 'Opening Stock'), ('finish', 'Closing Stock')], string='Type',
                                default='finish')
    compare_to = fields.Many2one('stock.ipv', string='Compare to', states={'done': [('readonly', True)]},
                                 default=_get_default_compare_to)
    previous_date = fields.Datetime(related='compare_to.date', string='Previous Date', store=True, readonly=True)
    included_categories = fields.Selection([
        ('all', 'All Categories'),
        ('important', 'Only Important Categories')
    ], string='Included Categories', default='important', states={'done': [('readonly', True)]})
    line_ids = fields.One2many('stock.ipv.line', 'ipv_id', string='Products', states={'done': [('readonly', True)]})

    @api.multi
    def _get_qty_start(self, product_id):
        self.ensure_one()
        if self.ipv_type == 'finish' and self.compare_to:
            line = self.compare_to.line_ids.filtered(lambda s: s.product_id.id == product_id)
            if len(line):
                return line[0].qty_end
        return 0

    @api.multi
    def _get_qty_in(self, product_id):
        self.ensure_one()
        if self.ipv_type == 'finish' and self.compare_to:
            in_domain = [
                ('product_id', '=', product_id),
                ('location_dest_id', '=', self.location_id.id),
                ('state', '=', 'done'),
                ('date', '>=', self.previous_date),
                ('date', '<=', self.date)
            ]
            in_moves = self.env['stock.move'].search(in_domain)
            if len(in_moves):
                return sum(in_moves.mapped('product_qty'))
        return 0

    @api.multi
    def _get_qty_out(self, product_id):
        self.ensure_one()
        if self.ipv_type == 'finish' and self.compare_to:
            out_domain = [
                ('product_id', '=', product_id),
                ('location_id', '=', self.location_id.id),
                ('state', '=', 'done'),
                ('date', '>=', self.previous_date),
                ('date', '<=', self.date)
            ]
            out_moves = self.env['stock.move'].search(out_domain)
            if len(out_moves):
                return sum(out_moves.mapped('product_qty'))
        return 0

    @api.multi
    def _generate_lines(self):
        self.ensure_one()
        quantities = self.location_id.get_real_stock()
        for product in self.env['product.product'].search([('type', '=', 'product')]):
            qty_start = self._get_qty_start(product.id)
            qty_in = self._get_qty_in(product.id)
            qty_out = self._get_qty_out(product.id)
            qty_end = quantities.get(product.id, 0)
            if any([qty_start, qty_in, qty_out, qty_end]):
                vals = {
                    'ipv_id': self.id,
                    'product_id': product.id,
                    'qty_start': qty_start,
                    'qty_in': qty_in,
                    'qty_out': qty_out,
                    'qty_end': qty_end
                }
                self.env['stock.ipv.line'].create(vals)

    def get_report_lines(self):
        lines = []
        cats = self.env['product.category'].search([])
        if self.included_categories == 'important':
            cats = cats.filtered(lambda s: s.important_to_print)
        for cat in cats:
            ipv_lines = self.line_ids.filtered(lambda s: s.categ_id.id == cat.id)
            if len(ipv_lines):
                products = []
                for l in ipv_lines:
                    if self.ipv_type == 'finish':
                        products.append([l.product_id.name, l.uom_id.name, l.qty_start, l.qty_in, l.qty_out, l.qty_end])
                    else:
                        products.append([l.product_id.name, l.uom_id.name, l.qty_end, '', '', ''])

                lines.append([cat.name, products])
        return lines

    @api.multi
    def action_print(self):
        self.ensure_one()
        if self.state == 'draft':
            self._generate_lines()
            self.state = 'done'
        action = self.env['report'].get_action(self, 'pos_stock.report_location_real_stock')
        return action


class IPVLine(models.Model):
    _name = 'stock.ipv.line'
    _rec_name = 'product_id'

    ipv_id = fields.Many2one('stock.ipv', string='IPV', required=True, ondelete='cascade')
    date = fields.Datetime(related='ipv_id.date', store=True, readonly=True)
    previous_date = fields.Datetime(related='ipv_id.previous_date', store=True, readonly=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, ondelete='cascade', readonly=True)
    categ_id = fields.Many2one(related='product_id.categ_id', store=True, readonly=True)
    uom_id = fields.Many2one(related='product_id.uom_id', store=True, readonly=True)

    qty_start = fields.Float(string='Start', readonly=True, digits=dp.get_precision('Product Unit of Measure'))
    qty_in = fields.Float(string='In', readonly=True, digits=dp.get_precision('Product Unit of Measure'))
    qty_out = fields.Float(string='Out', readonly=True, digits=dp.get_precision('Product Unit of Measure'))
    qty_end = fields.Float(string='End', readonly=True, digits=dp.get_precision('Product Unit of Measure'))


class ProductCategory(models.Model):
    _inherit = 'product.category'

    important_to_print = fields.Boolean(string='IPV important', help='Include as IPV important categories.',
                                        default=True)
