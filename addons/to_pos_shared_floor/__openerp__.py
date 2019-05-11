# -*- coding: utf-8 -*-

{
    'name': 'TO POS Shared Floor',
    'version': '1.0.0',
    'summary': 'Allow share multi floors to PoSes',
    'sequence': 24,
    'category': 'Point Of Sale',
    'description': """

    """,
    'depends': ['pos_restaurant'],
    'data': [
        'views/restaurant_view.xml',
        'views/templates.xml',
    ],
    'installable': True,
}
