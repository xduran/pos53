#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError


_logger = logging.getLogger(__name__)


class ProductProcessing(models.Model):
    _name = 'product.processing'

    name = fields.Char(string='Name', required=True, states={'done': [('readonly', True)]})
    note = fields.Text(string='Note', states={'done': [('readonly', True)]})
    date = fields.Date(string='Date', required=True, states={'done': [('readonly', True)]}, select=True,
                       copy=False, default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', string='Responsible', readonly=True, default=lambda s: s.env.user)
    state = fields.Selection(string="State", default='draft', selection=[('draft', 'Draft'), ('done', 'Done')])
    lines_in = fields.One2many('product.processing.line', 'processing_id', string='Products In',
                               domain=[('type', '=', 'in')], states={'done': [('readonly', True)]})
    lines_out = fields.One2many('product.processing.line', 'processing_id', string='Products Out',
                                domain=[('type', '=', 'out')], states={'done': [('readonly', True)]})
    picking_in = fields.Many2one('stock.picking', string='Picking in', select=True,
                                 states={'done': [('readonly', True)]})
    picking_out = fields.Many2one('stock.picking', string='Picking out', select=True,
                                  states={'done': [('readonly', True)]})
    picking_type_in_id = fields.Many2one('stock.picking.type', string='Picking In Type', required=True,
                                         states={'done': [('readonly', True)]},
                                         default=lambda s: s.env.ref('pos_stock.picking_type_to_production', False))
    picking_type_out_id = fields.Many2one('stock.picking.type', string='Picking Out Type', required=True,
                                          states={'done': [('readonly', True)]},
                                          default=lambda s: s.env.ref('pos_stock.picking_type_from_production', False))
    location_src_id = fields.Many2one('stock.location', string='Source Location', required=True, select=True,
                                      states={'done': [('readonly', True)]}, domain=[('usage', '=', 'internal')],
                                      default=lambda s: s.env.ref('stock.stock_location_stock', False))
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True, select=True,
                                       states={'done': [('readonly', True)]}, domain=[('usage', '=', 'internal')],
                                       default=lambda s: s.env.ref('stock.stock_location_stock', False))
    location_prod_id = fields.Many2one('stock.location', string='Production Location', required=True, select=True,
                                       states={'done': [('readonly', True)]},
                                       default=lambda s: s.env.ref('stock.location_production', False))

    def process_products(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        for item in self.browse(cr, uid, ids, context=context):
            # abort if no raw materials listed
            if len(item.lines_in) == 0:
                raise UserError(_('No raw materials listed.'))
            # abort if no finish products listed
            if len(item.lines_out) == 0:
                raise UserError(_('No finish products listed.'))
            # create picking to deliver raw materials to production
            picking_in_id = picking_obj.create(cr, uid, {
                'origin': "%s(%s)" % (item.name, item.date),
                'move_type': 'one',
                'picking_type_id': item.picking_type_in_id.id,
                'location_id': item.location_src_id.id,
                'location_dest_id': item.location_prod_id.id,
                'date': item.date,
                'date_done': item.date,
            }, context=context)
            self.write(cr, uid, [item.id], {'picking_in_id': picking_in_id}, context=context)
            for line in item.lines_in:
                if line.product_id and line.product_id.type not in ['product', 'consu']:
                    continue
                move_obj.create(cr, uid, {
                    'name':  line.product_id.name,
                    'origin':  "%s(%s)" % (item.name, item.date),
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking_in_id,
                    'picking_type_id': item.picking_type_in_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                    'state': 'draft',
                    'location_id': item.location_src_id.id,
                    'location_dest_id': item.location_prod_id.id,
                }, context=context)
            if picking_in_id:
                picking_obj.action_confirm(cr, uid, [picking_in_id], context=context)
                picking_obj.force_assign(cr, uid, [picking_in_id], context=context)
                # Mark pack operations as done
                pick = picking_obj.browse(cr, uid, picking_in_id, context=context)
                for pack in pick.pack_operation_ids:
                    self.pool['stock.pack.operation'].write(cr, uid, [pack.id], {'qty_done': pack.product_qty},
                                                            context=context)
                picking_obj.action_done(cr, uid, [picking_in_id], context=context)
            # create picking to receive finish products from production
            picking_out_id = picking_obj.create(cr, uid, {
                'origin': "%s(%s)" % (item.name, item.date),
                'move_type': 'one',
                'picking_type_id': item.picking_type_out_id.id,
                'location_id': item.location_prod_id.id,
                'location_dest_id': item.location_dest_id.id,
                'date': item.date,
                'date_done': item.date,
            }, context=context)
            self.write(cr, uid, [item.id], {'picking_out_id': picking_out_id}, context=context)
            for line in item.lines_out:
                if line.product_id and line.product_id.type not in ['product', 'consu']:
                    continue
                move_obj.create(cr, uid, {
                    'name':  line.product_id.name,
                    'origin':  "%s(%s)" % (item.name, item.date),
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking_out_id,
                    'picking_type_id': item.picking_type_out_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                    'state': 'draft',
                    'location_id': item.location_prod_id.id,
                    'location_dest_id': item.location_dest_id.id,
                }, context=context)
            if picking_out_id:
                picking_obj.action_confirm(cr, uid, [picking_out_id], context=context)
                picking_obj.force_assign(cr, uid, [picking_out_id], context=context)
                # Mark pack operations as done
                pick = picking_obj.browse(cr, uid, picking_out_id, context=context)
                for pack in pick.pack_operation_ids:
                    self.pool['stock.pack.operation'].write(cr, uid, [pack.id], {'qty_done': pack.product_qty},
                                                            context=context)
                picking_obj.action_done(cr, uid, [picking_out_id], context=context)
        return self.write(cr, uid, ids, {'state': 'done'}, context=context)


class ProductProcessingLine(models.Model):
    _name = 'product.processing.line'
    _rec_name = 'product_id'

    processing_id = fields.Many2one('product.processing', string='Product Processing', required=True)
    type = fields.Selection(string='Type', selection=[('in', 'In'), ('out', 'Out')], required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Float(string='Quantity', required=True, default=1)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True)

    def onchange_line(self, cr, uid, ids, product_id=False, uom_id=False, context=None):
        res = {'value': {}}
        if product_id:
            product = self.pool.get('product.template').browse(cr, uid, product_id, context=context)
            uom = self.pool['product.uom'].browse(cr, uid, uom_id, context=context)
            if product.uom_id.category_id.id != uom.category_id.id:
                res['value']['uom_id'] = product.uom_id.id
                res['domain'] = {'uom_id': [('category_id', '=', product.uom_id.category_id.id)]}
        return res

