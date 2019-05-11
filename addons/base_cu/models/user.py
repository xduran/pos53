# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import models

_logger = logging.getLogger(__name__)


class User(models.Model):
    _inherit = 'res.users'

    _defaults = {
        'notify_email': 'none',
    }
