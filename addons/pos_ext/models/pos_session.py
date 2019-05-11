# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
import pytz
import datetime
from openerp import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


_logger = logging.getLogger(__name__)


class POSSession(models.Model):
    _inherit = 'pos.session'

    session_cost = fields.Float(string='Cost', compute='_compute_cost', readonly=True, store=True)

    @api.multi
    @api.depends('order_ids')
    def _compute_cost(self):
        for session in self:
            cost = 0
            for order in session.order_ids:
                cost += order.order_cost
            session.session_cost = cost
