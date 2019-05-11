#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from lxml import etree
from openerp import api, fields, models, _


_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _default_picking_type(self):
        company_id = self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
        return warehouse.int_type_id

    picking_type_id = fields.Many2one(default=lambda self: self._default_picking_type())

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(StockPicking, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                        submenu=submenu)
        if self._context.get('internal_only', False) and view_type == 'form':
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='location_id']"):
                node.set('domain', "[('usage', '=', 'internal')]")
            for node in doc.xpath("//field[@name='location_dest_id']"):
                node.set('domain', "[('usage', '=', 'internal')]")
            res['arch'] = etree.tostring(doc)
        return res

