# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'Purchase Simplification',
    'version': '0.1',
    'author': 'Javier Ruiz Durán',
    'summary': 'Hide menus, actions and fields to simplify the purchase module',
    'description': """

    """,
    'category': 'Purchase',
    'website': '',
    'depends': ['purchase'],
    'data': [
        'views/purchase_simplification_view.xml',
        'data/purchase_order_line_data.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        
    ],
    'installable': True,
    'auto_install': False,
}
