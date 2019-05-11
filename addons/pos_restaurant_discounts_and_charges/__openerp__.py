# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS Discounts and Fees',
    'version': '1.0',
    'author': 'Javier Ruiz Durán',
    'category': 'Point of Sale',
    'summary': 'Apply global discounts and Fees to orders.',
    'description': """
POS Discounts and Fees
====================================

Details...

    """,
    'depends': ['pos_ext'],
    'data': [
        'views/templates.xml',
        'views/discounts_and_fees_view.xml',
    ],
    'demo': [

    ],
    'test': [

    ],
    'qweb': [
        'static/src/xml/discounts_and_fees.xml',
    ],
    'website': '',
    'auto_install': False,
    'installable': True,
    'application': False,
}
