# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'Restaurant Extension',
    'version': '0.1',
    'author': 'Javier Ruiz Durán',
    'summary': 'Extension of Restaurant module',
    'description': """
Restaurant Extension
====================

Details...

    """,
    'category': 'Point of Sale',
    'website': '',
    'depends': ['pos_restaurant', 'pos_ext', 'pos_garnish'],
    'data': [
        'security/ir.model.access.csv',
        'data/pos_category_data.xml',
        'data/pos_config_data.xml',
        'views/settings_view.xml',
        'views/pos_order_line_view.xml',
        'views/pos_config_view.xml',
        'views/pos_waiter_view.xml',
        'views/pos_order_view.xml',
        'views/pos_session_view.xml',
        'views/menu_view.xml',
        'views/templates.xml',
        'report/pos_order_report_view.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        'static/src/xml/change_table.xml',
        'static/src/xml/posticket_ext.xml',
        'static/src/xml/waiter.xml',
        'static/src/xml/multiprint_ext.xml',
    ],
    'installable': True,
    'auto_install': True,
}
