# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS Stock',
    'version': '0.1',
    'author': 'Javier Ruiz Durán',
    'summary': 'Point of Sale Inventory',
    'description': """
POS Stock
=========

Details...

    """,
    'category': 'Point of Sale',
    'website': '',
    'depends': ['point_of_sale'],
    'data': [
        'security/stock_security.xml',
        'security/ir.model.access.csv',
        'data/stock_data.xml',
        'data/pos_config_data.xml',
        'data/uom_data.xml',
        'views/product_processing_view.xml',
        'views/stock_recover_view.xml',
        'views/stock_locations_view.xml',
        'views/stock_inventory_view.xml',
        'views/stock_picking_view.xml',
        'views/report_location_real_stock.xml',
        'views/stock_move_analysis_view.xml',
        'views/stock_ipv_view.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        
    ],
    'installable': True,
    'auto_install': True,
}
