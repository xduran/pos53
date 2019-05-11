# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'Restaurant Work Orders',
    'version': '0.1',
    'author': 'Javier Ruiz Durán',
    'summary': 'Follow up customers orders.',
    'description': """
Restaurant Work Orders
======================

Details...

    """,
    'category': 'Point of Sale',
    'website': '',
    'depends': ['pos_restaurant_ext', 'web_ext', 'pos_garnish'],
    'data': [
        'data/work_order_stage_data.xml',
        'data/restaurant_printer_data.xml',
        'data/pos_config_data.xml',
        'security/ir.model.access.csv',
        'views/work_order_view.xml',
        'views/templates.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        'static/src/xml/work_order.xml',
    ],
    'installable': True,
    'auto_install': False,
}
