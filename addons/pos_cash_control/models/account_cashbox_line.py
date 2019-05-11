#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _

_logger = logging.getLogger(__name__)


class AccountCashboxLine(models.Model):
    _inherit = 'account.cashbox.line'

    coin_value = fields.Many2one('currency.values', string='Coin/Bill Value', required=True)
    
    @api.one
    @api.depends('coin_value', 'number')
    def _sub_total(self):
        """ Calculates Sub total"""
        self.subtotal = self.coin_value.value * self.number


class AccountBankStmtCashWizard(models.Model):
    """
    Account Bank Statement popup that allows entering cash details.
    """
    _inherit = 'account.bank.statement.cashbox'

    def _default_cashbox_lines(self):
        coin_values = self.env['currency.values'].search([])
        return [[0, False, {'coin_value': x, 'number': 0, 'subtotal': 0}] for x in coin_values]

    cashbox_lines_ids = fields.One2many(default=_default_cashbox_lines)