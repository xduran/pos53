#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


_logger = logging.getLogger(__name__)


class POSCategory(models.Model):
    _inherit = 'pos.category'

    is_garnish = fields.Boolean(string="Is garnish", default=False)


class ProductGarnish(models.Model):
    _name = 'product.garnish'

    product_id = fields.Many2one('product.template', string='Product', required=True,
                                 domain=[('to_garnish', '=', True)])
    garnish_id = fields.Many2one('product.template', string='Garnish', required=True,
                                 domain=[('is_garnish', '=', True)])
    price_extra = fields.Float(string='Extra Price', digits_compute=dp.get_precision('Product Price'))
    name = fields.Char(related='garnish_id.name')
    active = fields.Boolean(related='garnish_id.active', store=True)

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary(related='garnish_id.image')
    image_medium = fields.Binary(related='garnish_id.image_medium')
    image_small = fields.Binary(related='garnish_id.image_small')


class Product(models.Model):
    _inherit = 'product.template'

    to_garnish = fields.Boolean(string="Allow garnish", default=False,
                                help="Allows to specify product's garnish. Very common in restaurants main dishes.")
    order_separated = fields.Boolean(string="Order separated", default=True,
                                     help="Print the garnishes as individual orders.")
    stand_alone = fields.Boolean(string="Stand Alone", default=True,
                                 help="Indicates that the product can be sold independently, "
                                      "regardless if it is a garnish.")
    allowed_garnish = fields.Integer(string="Number of garnish", default=1,
                                     help="Maximum number of allowed garnish to serve with each unit of the product.")
    valid_garnish_ids = fields.One2many('product.garnish', 'product_id', string='Valid garnish',
                                        help="When you sell this product, you will be ask to chose the garnish of "
                                             "the product among this options.")
    garnish_of_ids = fields.One2many('product.garnish', 'garnish_id', string='Garnish of',
                                     help="Products that can be serve with this one as a garnish.")
    is_garnish = fields.Boolean(related='pos_categ_id.is_garnish')

    def _write(self, cr, uid, ids, values, context=None):
        if values.get('is_garnish', False):
            values['to_garnish'] = False
            values['allowed_garnish'] = 1
            product_garnish_obj = self.pool.get('product.garnish')
            product_garnish_ids = product_garnish_obj.search(cr, uid, [('product_id', 'in', ids)], context=context)
            product_garnish_obj.unlink(cr, uid, product_garnish_ids, context=context)
            if values.get('valid_garnish_ids', False):
                del values['valid_garnish_ids']

        return super(Product, self)._write(cr, uid, ids, values, context=context)

    def _create(self, cr, uid, values, context=None):
        if values.get('pos_categ_id', False):
            pos_category_obj = self.pool.get('pos.category')
            pos_category = pos_category_obj.browse(cr, uid, values['pos_categ_id'], context=context)
            if pos_category.is_garnish:
                if values.get('to_garnish', False):
                    values['to_garnish'] = False
                if values.get('allowed_garnish', False):
                    values['allowed_garnish'] = 1
                if values.get('valid_garnish_ids', False):
                    del values['valid_garnish_ids']

        return super(Product, self)._create(cr, uid, values, context=context)


class POSOrderLineGarnish(models.Model):
    _name = 'pos.order.line.garnish'
    _rec_name = 'garnish_id'

    order_line_id = fields.Many2one('pos.order.line', string='Line', ondelete='cascade')
    garnish_id = fields.Many2one('product.template', string='Garnish', required=True)
    price_extra = fields.Float(string='Price Extra')

    @api.multi
    @api.depends('garnish_id')
    def name_get(self):
        result = []
        for garnish_line in self:
            name = garnish_line.garnish_id.name
            result.append((garnish_line.id, name))
        return result


class POSOrderLine(models.Model):
    _inherit = "pos.order.line"

    product_garnish_ids = fields.One2many('pos.order.line.garnish', 'order_line_id', string='Product garnish',
                                          help="Selected garnish for the product.")
    garnish_text = fields.Char(string='Garnish', compute='_fields_compute', readonly=True)

    @api.multi
    def _fields_compute(self):
        for order_line in self:
            garnish_text = ""
            garnish_names = [g.garnish_id.name for g in order_line.product_garnish_ids]
            if garnish_names:
                garnish_text = "(" + ', '.join(garnish_names) + ")"
            order_line.garnish_text = garnish_text

    def _order_line_fields(self, cr, uid, line, context=None):
        if 'garnish' in line[2]:
            garnish_ids = line[2]['garnish']
            del line[2]['garnish']
            product_garnish_ids = []
            for x in garnish_ids:
                product_garnish = self.pool.get('product.garnish').browse(cr, uid, x, context=context)
                product_garnish_ids.append([0, False, {
                    'order_line_id': False,
                    'garnish_id': product_garnish.garnish_id.id,
                    'price_extra': product_garnish.price_extra
                }])
            line[2]['product_garnish_ids'] = product_garnish_ids
        return super(POSOrderLine, self)._order_line_fields(cr, uid, line, context=context)


class POSOrder(models.Model):
    _inherit = "pos.order"

    def _get_product_quantities(self, cr, uid, ids, context=None):
        product_qtys = super(POSOrder, self)._get_product_quantities(cr, uid, ids, context=context)
        product_obj = self.pool.get('product.template')
        sequence_obj = self.pool.get('ir.sequence')
        for order in self.browse(cr, uid, ids, context=context):
            garnish_product = {}
            for line in order.lines:
                if len(line.product_garnish_ids):
                    for garnish in line.product_garnish_ids:
                        if garnish.garnish_id.id in garnish_product:
                            garnish_product[garnish.garnish_id.id] += abs(line.qty)
                        else:
                            garnish_product[garnish.garnish_id.id] = abs(line.qty)
            for key in garnish_product.iterkeys():
                product_qtys.append({
                    'name': sequence_obj.next_by_code(cr, uid, 'pos.order.line', context=context),
                    'product_uom': product_obj.browse(cr, uid, key, context=context).uom_id.id,
                    'product_id': key,
                    'product_uom_qty': garnish_product[key],
                })
        return product_qtys


class POSConfig(models.Model):
    _inherit = 'pos.config'

    iface_garnish = fields.Boolean(string="Garnish", help="Allows to specify product's garnish", default=True)

