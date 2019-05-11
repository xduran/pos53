# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'Product Garnish',
    'version': '0.1',
    'author': 'Javier Ruiz Durán',
    'summary': 'Allow Garnish of Products',
    'description': """
Product Garnish
===============

Details...

    """,
    'category': 'Point of Sale',
    'website': '',
    'depends': ['pos_ext', 'pos_restaurant'],
    'data': [
        'data/pos_config_data.xml',
        'security/ir.model.access.csv',
        'views/garnish_view.xml',
        'views/templates.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        'static/src/xml/garnish.xml',
    ],
    'installable': True,
    'auto_install': False,
}
