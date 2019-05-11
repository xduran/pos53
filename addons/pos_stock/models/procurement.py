#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _


_logger = logging.getLogger(__name__)


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def write(self, vals):
        if 'state' in vals and vals.get('state') == 'exception':
            vals['state'] = 'cancel'
        return super(ProcurementOrder, self).write(vals)
