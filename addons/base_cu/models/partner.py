# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, tools, fields, models, _

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    country_id = fields.Many2one(default=lambda self: self.env.ref('base.cu'))
    state_id = fields.Many2one(default=lambda self: self.env.ref('base_cu.hab'))
    county_id = fields.Many2one('res.country.state.county', string="County", ondelete='restrict')
    city = fields.Char(related='county_id.name', store=True)
