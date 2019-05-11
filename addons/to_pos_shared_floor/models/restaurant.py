# -*- coding: utf-8 -*-

from openerp import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    floor_ids = fields.Many2many('restaurant.floor', 'pos_config_floor_rel', 'pos_config_id', 'floor_id', string="Restaurant Floors", help='The restaurant floors served by this point of sale')
