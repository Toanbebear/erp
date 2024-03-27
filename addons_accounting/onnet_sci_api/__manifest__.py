# -*- coding: utf-8 -*-

{
    'name': 'Accounting api',
    'author': 'TaiHT',
    'depends': ['account', 'purchase', 'sale'],
    'data': [
        'data/ir_config_param.xml',
        'views/api_log.xml',
        'views/records_com_ent_rel.xml',
        'views/product_category_views.xml',
        'views/model_line_views.xml',
        'views/account_move.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
