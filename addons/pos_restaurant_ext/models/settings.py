# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, tools, fields, models, _

_logger = logging.getLogger(__name__)


class POSConfiguration(models.TransientModel):
    _inherit = 'pos.config.settings'

    # TODO: Move this parameter to pos_ext module
    module_pos_garnish = fields.Boolean(string='Product Garnish',
                                        help="If you check this box, you will be able to use garnish for your "
                                             "products.")
    module_pos_restaurant_changes_control = fields.Boolean(string='Changes Control',
                                                           help="If you check this box, you will be able keep track "
                                                                "of changes made to orders after printed.")
    # TODO: Move this parameter to pos_ext module
    module_pos_restaurant_work_orders = fields.Boolean(string='Work Center',
                                                       help="If you check this box, you will be able see the customers "
                                                            "orders before they paid from a category oriented screen. "
                                                            "This allows you to inform your work centers "
                                                            "(i.e. Kitchen, Bar) of the customer orders and keep track "
                                                            "of their statuses.""")


