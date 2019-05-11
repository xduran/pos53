#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _

_logger = logging.getLogger(__name__)


class POSConfig(models.Model):
    _inherit = 'pos.config'

    iface_change_cashier = fields.Boolean(string="Change Cashier", help="Allows to change the cashier", default=False)

    iface_change_price = fields.Boolean(string="Change Price", help="Allows to change the price of products",
                                        default=True)
    iface_change_discount = fields.Boolean(string="Change Discount", help="Allows to change the discount of products",
                                           default=True)
    iface_change_sing = fields.Boolean(string="Change Sing", help="Allows to use negative numbers", default=True)

    active_session = fields.Many2one('pos.session', string="Active Session", compute='_get_active_session')

    @api.multi
    def _get_active_session(self):
        for pos_config in self:
            session_id = pos_config.session_ids.filtered(lambda r: not r.state == 'closed' and not r.rescue)
            pos_config.active_session = session_id
