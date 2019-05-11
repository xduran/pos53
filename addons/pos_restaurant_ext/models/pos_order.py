# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import fields, models, _


_logger = logging.getLogger(__name__)


class POSOrder(models.Model):
    _inherit = "pos.order"

    waiter_id = fields.Many2one('pos.waiter', string='Waiter')

    def _order_fields(self, cr, uid, ui_order, context=None):
        order_fields = super(POSOrder, self)._order_fields(cr, uid, ui_order, context=context)
        order_fields['waiter_id'] = ui_order.get('waiter_id', False)
        return order_fields
