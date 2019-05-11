# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import fields, models, _

_logger = logging.getLogger(__name__)


class POSWaiter(models.Model):
    _name = "pos.waiter"

    name = fields.Char(string='Name', required=True)
