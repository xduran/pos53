# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'Restaurant Changes Control',
    'version': '0.1',
    'author': 'Javier Ruiz Durán',
    'summary': 'Keep track of changes in order lines',
    'description': """
Restaurant Changes Control
==========================

Details...

    """,
    'category': 'Point of Sale',
    'website': '',
    'depends': ['pos_restaurant_ext'],
    'data': [
        'data/pos_config_data.xml',
        'security/ir.model.access.csv',
        'views/changes_control_view.xml',
        'views/templates.xml',
    ],
    'demo': [
        
    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,
}
