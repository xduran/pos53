# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

{
    'name': 'Cuban Base Extension',
    'version': '0.1',
    'author': 'Javier Ruiz Durán',
    'summary': 'Extension of Odoo base module for Cuba',
    'description': """
Cuban Base Extension
====================

This module modify the odoo base module for the Odec Suite purposes.

    """,
    'category': 'Hidden',
    'website': '',
    'depends': ['base'],
    'data': [

        'data/language_data.xml',
        'data/user_data.xml',
        'data/states_data.xml',
        'data/currency_data.xml',
        'data/company_data.xml',
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/res_country_state_view.xml',
        'views/res_country_state_county_view.xml',
    ],
    'demo': [

    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': True,
}
