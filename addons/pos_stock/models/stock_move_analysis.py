#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


_logger = logging.getLogger(__name__)


class StockMoveAnalysis(models.Model):
    _name = 'stock.move.analysis'

    name = fields.Char(compute='_compute_name')
    location_id = fields.Many2one('stock.location', string='Location', required=True,
                                  states={'done': [('readonly', True)]})
    start_date = fields.Datetime(string='Start', required=True, states={'done': [('readonly', True)]})
    end_date = fields.Datetime(string='End', required=True, states={'done': [('readonly', True)]})
    use_expected_date = fields.Boolean(string='Use expected date', states={'done': [('readonly', True)]})
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', readonly=True,
                             default='draft', track_visibility='onchange')

    in_value = fields.Float(string='In Value', digits=dp.get_precision('Product Price'), compute='_make_analysis',
                            store=True)
    out_value = fields.Float(string='Out Value', digits=dp.get_precision('Product Price'), compute='_make_analysis',
                             store=True)
    net_value = fields.Float(string='Net Value', digits=dp.get_precision('Product Price'), compute='_make_analysis',
                             store=True)

    in_moves_domain = fields.Char(compute='_make_analysis', store=True)
    out_moves_domain = fields.Char(compute='_make_analysis', store=True)

    @api.one
    @api.depends('location_id', 'start_date', 'end_date')
    def _compute_name(self):
        self.name = "%s [%s - %s]" % (self.location_id.name, self.start_date, self.end_date)

    @api.one
    @api.depends('state')
    def _make_analysis(self):
        if self.state == 'done' and self.location_id and self.start_date and self.end_date:
            in_domain = [('location_dest_id', '=', self.location_id.id), ('state', '=', 'done')]
            out_domain = [('location_id', '=', self.location_id.id), ('state', '=', 'done')]
            if self.use_expected_date:
                date_range = [('date_expected', '>=', self.start_date), ('date_expected', '<=', self.end_date)]
            else:
                date_range = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]
            in_domain.extend(date_range)
            out_domain.extend(date_range)

            self.in_moves_domain = in_domain
            self.out_moves_domain = out_domain

            in_moves = self.env['stock.move'].search(in_domain)
            out_moves = self.env['stock.move'].search(out_domain)

            self.in_value = sum(in_moves.mapped('move_value'))
            self.out_value = sum(out_moves.mapped('move_value'))
            self.net_value = self.in_value - self.out_value

    @api.multi
    def open_in_moves(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('pos_stock', 'action_stock_move_tree')
        action['domain'] = self.in_moves_domain
        return action

    @api.multi
    def open_out_moves(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window'].for_xml_id('pos_stock', 'action_stock_move_tree')
        action['domain'] = self.out_moves_domain
        return action

    @api.multi
    def action_analysis(self):
        self.state = 'done'
        return {}
