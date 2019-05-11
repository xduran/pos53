# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product Garnish Cost',
    'version': '0.1',
    'author': 'Javier Ruiz Durán',
    'summary': 'Cost of garnish',
    'description': """
Product Garnish Cost
====================

Details...

    """,
    'category': 'Point of Sale',
    'website': '',
    'depends': ['pos_garnish'],
    'data': [
        'views/garnish_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        
    ],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}
