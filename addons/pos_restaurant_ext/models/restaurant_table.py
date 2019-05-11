# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, tools, fields, models, _

_logger = logging.getLogger(__name__)


class RestaurantFloor(models.Model):
    _inherit = 'restaurant.floor'

    name = fields.Char(translate=True)


class RestaurantTable(models.Model):
    _inherit = 'restaurant.table'

    name = fields.Char(translate=True)


class POSConfig(models.Model):
    _inherit = 'pos.config'

    iface_change_table = fields.Boolean(string="Change table", help="Allows to change order's table", default=True)
    iface_guest_count = fields.Boolean(string="Guest Count", help="Allows to specify guest count", default=True)
    iface_waiter = fields.Boolean(string="Waiter", help="Allows to specify the waiter that serves the table",
                                  default=True)
