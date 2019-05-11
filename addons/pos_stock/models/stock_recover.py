#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


_logger = logging.getLogger(__name__)


class StockRecover(models.Model):
    _name = 'stock.recover'
    _description = "Recover"
    
    _rec_name = 'location_dest_id'
    
    RECOVER_STATE_SELECTION = [
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('done', 'Validated'),
    ]

    location_id = fields.Many2one('stock.location', 'Source Location Zone', required=True, readonly=True, states={'draft': [('readonly', False)]})
    location_dest_id = fields.Many2one('stock.location', 'Destination Location Zone', required=True, readonly=True)
    categ_id = fields.Many2one('product.category', string='Product Category', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(RECOVER_STATE_SELECTION, 'Status', readonly=True, select=True, copy=False, default='draft')
    line_ids = fields.One2many('stock.recover.line', 'recover_id', 'Recoveries', readonly=True, copy=True)
    date = fields.Datetime('Recover Date', required=True, readonly=True, default=lambda self: fields.datetime.now())
    picking_id = fields.Many2one('stock.picking', string='Picking', select=True)
    
    def prepare_recover(self, cr, uid, ids, context=None):
        recover_line_obj = self.pool.get('stock.recover.line')
        product_obj = self.pool.get('product.product')
        product_category_obj = self.pool.get('product.category')
        for recover in self.browse(cr, uid, ids, context=context):
            # If there are recover lines already (e.g. from import), respect those and set their theoretical qty
            line_ids = [line.id for line in recover.line_ids]
            if not line_ids:
                #compute the recover lines and create them
                vals = self._get_recover_lines(cr, uid, recover, context=context)
                for product_line in vals:
                    product = product_obj.browse(cr, uid, product_line['product_id'], context=context)
                    if recover.categ_id:
                        product_category_ids = product_category_obj.search(cr, uid, [('id', 'child_of', [recover.categ_id.id])], context=context)
                        if product.categ_id.id in product_category_ids:
                            recover_line_obj.create(cr, uid, product_line, context=context)
                    else:
                        recover_line_obj.create(cr, uid, product_line, context=context)
        return self.write(cr, uid, ids, {'state': 'confirm'})
     
    def _get_recover_lines(self, cr, uid, recover, context=None):
        location_obj = self.pool.get('stock.location')
        product_obj = self.pool.get('product.product')
        location_ids = location_obj.search(cr, uid, [('id', 'child_of', [recover.location_dest_id.id])], context=context)
        domain = ' location_id in %s'
        args = (tuple(location_ids),)
 
        cr.execute('''
           SELECT product_id, sum(qty) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
           FROM stock_quant WHERE''' + domain + '''
           GROUP BY product_id, location_id, lot_id, package_id, partner_id
        ''', args)
        vals = []
        for product_line in cr.dictfetchall():
            #replace the None the dictionary by False, because false values are tested later on
            for key, value in product_line.items():
                if not value:
                    product_line[key] = False
            product_line['recover_id'] = recover.id
            if product_line['product_id']:
                product = product_obj.browse(cr, uid, product_line['product_id'], context=context)
                product_line['product_uom_id'] = product.uom_id.id
            if product_line['product_qty'] < 0:
                vals.append(product_line)
            product_line['product_qty'] = abs(product_line['product_qty'])
        return vals
    
    def action_cancel_recover(self, cr, uid, ids, context=None):
        """ Change recover state to draft.
        @return: True
        """
        for recover in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [recover.id], {'line_ids': [(5,)], 'state': 'draft'}, context=context)
        return True
    
    def action_done(self, cr, uid, ids, context=None):
        """ Finish the recover
        @return: True
        """
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        for recover in self.browse(cr, uid, ids, context=context):
            # create picking to transfer materials
            picking_id = picking_obj.create(cr, uid, {
                'origin': "Recover (%s)" % (recover.date),
                'move_type': 'one',
                'picking_type_id': recover.location_dest_id.picking_in_type_default.id,
                'location_id': recover.location_id.id,
                'location_dest_id': recover.location_dest_id.id,
                'date': recover.date,
                'date_done': recover.date,
            }, context=context)
            self.write(cr, uid, [recover.id], {'picking_id': picking_id}, context=context)
            for line in recover.line_ids:
                if line.product_id and line.product_id.type not in ['product', 'consu']:
                    continue
                move_obj.create(cr, uid, {
                    'name':  line.product_id.name,
                    'origin':  "Recover (%s)" % (recover.date),
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking_id,
                    'picking_type_id': recover.location_dest_id.picking_in_type_default.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.product_qty),
                    'state': 'draft',
                    'location_id': recover.location_id.id,
                    'location_dest_id': recover.location_dest_id.id,
                }, context=context)
            if picking_id:
                picking_obj.action_confirm(cr, uid, [picking_id], context=context)
                picking_obj.force_assign(cr, uid, [picking_id], context=context)
                # Mark pack operations as done
                pick = picking_obj.browse(cr, uid, picking_id, context=context)
                for pack in pick.pack_operation_ids:
                    self.pool['stock.pack.operation'].write(cr, uid, [pack.id], {'qty_done': pack.product_qty},
                                                            context=context)
                picking_obj.action_done(cr, uid, [picking_id], context=context)
            self.write(cr, uid, [recover.id], {'state': 'done'}, context=context)
        return True

    
class StockRecoverLine(models.Model):
    _name = 'stock.recover.line'
    _description = "Recover Line"
     
    recover_id = fields.Many2one('stock.recover', 'Recover', ondelete='cascade', select=True)
    product_id = fields.Many2one('product.product', 'Product', required=True, select=True)
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure', required=True)
    product_qty = fields.Float('Transfer Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), default=0.0)
    
    