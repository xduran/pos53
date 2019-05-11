#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


_logger = logging.getLogger(__name__)


class Area(models.Model):
    _name = 'pos.area'
    _order = 'sequence asc'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer(string='Sequence')
    # location_id = fields.Many2one('stock.location', string='Location', domain=[('usage', '=', 'internal')])


class Product(models.Model):
    _inherit = 'product.template'

    area_id = fields.Many2one('pos.area', string='Area')


class AreaLocationMap(models.Model):
    _name = 'pos.area.location.rule'

    config_id = fields.Many2one('pos.config', string='Point of Sale')
    area_id = fields.Many2one('pos.area', string='Area')
    location_id = fields.Many2one('stock.location', string='Location', domain=[('usage', '=', 'internal')])


class POSConfig(models.Model):
    _inherit = 'pos.config'

    area_location_rules = fields.One2many('pos.area.location.rule', 'config_id', string='Area Location Rules')
