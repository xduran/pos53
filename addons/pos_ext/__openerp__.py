# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS Extension',
    'version': '0.1',
    'author': 'Javier Ruiz Durán',
    'summary': '',
    'description': """
Point of Sale Extension
=======================

Details...

    """,
    'category': 'Point of Sale',
    'website': '',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/pos_session_view.xml',
        'views/product_view.xml',
        'views/area_view.xml',
        'views/templates.xml',
        'report/pos_order_report_view.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        'static/src/xml/numpad_ext.xml',
        'static/src/xml/posticket_ext.xml',
        'static/src/xml/chrome_ext.xml',
        'static/src/xml/order_notes.xml',
    ],
    'installable': True,
    'auto_install': False,
}
