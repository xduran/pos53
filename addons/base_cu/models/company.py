# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    county_id = fields.Many2one('res.country.state.county', string='County')

    @api.onchange('country_id')
    def _onchange_country(self):
        self.ensure_one()
        self.state_id = False
        self.county_id = False
        return {'domain': {
            'state_id': [('country_id', '=', self.country_id)]
        }}

    @api.onchange('state_id')
    def _onchange_state(self):
        self.ensure_one()
        self.county_id = False
        return {'domain': {
            'city_id': [('state_id', '=', self.state_id)]
        }}
