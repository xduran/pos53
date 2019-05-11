# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _
from openerp.exceptions import UserError


_logger = logging.getLogger(__name__)


class BillOfMaterial(models.Model):
    _inherit = 'mrp.bom'

    type = fields.Selection(default='phantom')
    cost = fields.Float(string='Cost', compute='_compute_cost', readonly=True, store=True)

    @api.multi
    @api.depends('bom_line_ids', 'bom_line_ids.cost')
    def _compute_cost(self):
        for bom in self:
            bom.cost = sum([l.cost for l in bom.bom_line_ids])

    @api.multi
    def action_assign_product_cost(self):
        self.ensure_one()
        self.product_tmpl_id.standard_price = self.cost
        return True


class BillOfMaterialLine(models.Model):
    _inherit = 'mrp.bom.line'

    cost = fields.Float(string='Cost', compute='_compute_cost', readonly=True, store=True)

    @api.multi
    @api.depends('product_id', 'product_qty', 'product_uom', 'product_id.standard_price')
    def _compute_cost(self):
        uom_obj = self.env['product.uom']
        for line in self:
            qty = line.product_qty
            if line.product_id.uom_id.id != line.product_uom.id:
                if line.product_id.uom_id.category_id.id != line.product_uom.category_id.id:
                    print '###################################'
                    # print "##################### %s linea %s" % (line.bom_id.product_tmpl_id.name, line.product_id.name)
                    #raise UserError(_('The UoM used for %s in BoM of %s does not belong to the same'
                    #                   ' category of the UoM set in the product.')
                    #                 % (line.product_id.name, line.bom_id.product_tmpl_id.name))
                else:
                    qty = uom_obj._compute_qty(line.product_uom.id, qty, line.product_id.uom_id.id)
            line.cost = line.product_id.standard_price * qty



class Product(models.Model):
    _inherit = 'product.template'

    used_count = fields.Integer(string='# Bill of Material', compute="_used_count")

    @api.multi
    def _used_count(self):
        for product in self:
            product.used_count = self.env['mrp.bom.line'].search_count([('product_id', '=', product.id)])

    @api.multi
    def action_used_in_bom(self):
        ctx = self._context.copy()
        # model = 'mrp.bom'

        bom_lines_ids = self.env['mrp.bom.line'].search([('product_id', '=', self.id)]).ids
        bom_list = [item.bom_id.id for item in self.env['mrp.bom.line'].browse(bom_lines_ids)]

        # view_id = self.env.ref('mrp.mrp_bom_tree_view').id
        domain = "[('id','in', %s)]" % str(bom_list)

        result = self._get_act_window_dict('mrp.mrp_bom_form_action', context=ctx)
        result['domain'] = domain

        return result
        # return {
        #     'name': self.name,
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'tree',
        #     'res_model': model,
        #     'view_id': view_id,
        #     'domain': domain,
        #     'context': ctx,
        # }

