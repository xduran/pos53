#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _

_logger = logging.getLogger(__name__)


class CurrencyValues(models.Model):
    _name = 'currency.values'
    _description = 'Currency Values'
    _order = 'sequence asc'

    name = fields.Char('Name', required=True)
    value = fields.Float(string='Value', required=True, digits=(12, 6))
    sequence = fields.Integer(string='Sequence')
    active = fields.Boolean(default=True)
