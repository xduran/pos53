#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _

_logger = logging.getLogger(__name__)


class POSSession(models.Model):
    _inherit = 'pos.session'

    customers_count = fields.Integer(string='Total Customers', compute='_compute_customers', readonly=True,
                                     help='The total number of customers.', store=True)

    @api.multi
    @api.depends('order_ids')
    def _compute_customers(self):
        for session in self:
            session.customers_count = sum([x.customer_count for x in session.order_ids])
