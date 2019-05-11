# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import fields, models, _

_logger = logging.getLogger(__name__)


class POSOrderLine(models.Model):
    _inherit = "pos.order.line"

    note = fields.Text(string='Note', readonly=True)
