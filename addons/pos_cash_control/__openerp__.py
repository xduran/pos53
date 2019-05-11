# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS Cash Control',
    'version': '0.1',
    'author': 'Joan Jon Iglesia',
    'summary': '',
    'description': """
POS Cash Control
=======================

Details...

    """,
    'category': 'Point of Sale',
    'website': '',
    'depends': ['pos_ext', 'pos_restaurant_discounts_and_charges'],
    'data': [
        'data/currency_values_data.xml',
        'data/cash_box_reason_data.xml',
        'data/account_bank_statement_data.xml',
        'security/ir.model.access.csv',
        'wizard/pos_box.xml',
        'views/cash_box_reason_view.xml',
        'views/currency_values_view.xml',
        'views/account_bank_statement_cashbox_view.xml',
        'views/account_bank_statement_view.xml',
        'views/pos_session_view.xml',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'report/cash_report_view.xml',
    ],
    'demo': [
        
    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,
}
