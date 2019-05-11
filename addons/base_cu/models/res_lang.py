# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, tools, fields, models, _

_logger = logging.getLogger(__name__)


class Language(models.Model):
    _inherit = 'res.lang'

    def fix_es_lang(self, cr, uid, **args):
        lang = 'es_ES'
        lang_ids = self.search(cr, uid, [('code', '=', lang)])
        if not lang_ids:
            self.load_lang(cr, uid, lang)
            lang_ids = self.search(cr, uid, [('code', '=', lang)])
        self.write(cr, uid, lang_ids, {'decimal_point': '.', 'thousands_sep': ''})
