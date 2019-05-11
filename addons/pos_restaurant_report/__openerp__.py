# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Restaurant Report',
    'version': '1.0.1',
    'category': 'Point of Sale',
    'sequence': 20,
    'summary': 'Summaries from point of sale.',
    'description': """
POS Restaurant Report
=====================

Details...

""",
    'depends': ['pos_restaurant_ext', 'pos_restaurant_discounts_and_charges', 'pos_garnish'],
    'data': [
        'data/report_paperformat.xml',
        'pos_restaurant_report.xml',
        'views/report_session_receipt.xml',
        'views/report_session_full_report.xml',
        'views/pos_session_view.xml',
        'views/report_receipt.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': False,
    'qweb': [],
    'website': '',
    'auto_install': False,
}
