# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, tools, fields, models, _

_logger = logging.getLogger(__name__)


class County(models.Model):
    _name = 'res.country.state.county'
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True, size=3)
    state_id = fields.Many2one('res.country.state', string="Province", requiered=True)
    country_id = fields.Many2one(related='state_id.country_id')


class State(models.Model):
    _inherit = 'res.country.state'

    county_ids = fields.One2many('res.country.state.county', 'state_id', string='Counties')
