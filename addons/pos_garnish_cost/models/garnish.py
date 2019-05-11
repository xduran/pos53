#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _


_logger = logging.getLogger(__name__)


class ProductGarnish(models.Model):
    _inherit = 'product.garnish'

    category = fields.Many2one(related='garnish_id.pos_categ_id', store=True)
    sale_price = fields.Float(related='garnish_id.list_price')
    cost = fields.Float(related='garnish_id.standard_price')
