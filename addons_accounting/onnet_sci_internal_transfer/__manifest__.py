# -*- coding: utf-8 -*-

{
    'name': 'SCI Internal Transfer',
    'author': 'TaiHT',
    'depends': ['stock', 'account', 'onnet_sci_allocation_rate'],
    'data': [
        'views/view_picking_view.xml',
        'views/res_config_settings_views.xml',
        'views/account_journal.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
