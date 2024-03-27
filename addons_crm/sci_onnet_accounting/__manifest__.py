{
    'name': 'SCI-Onnet: Accounting',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'author': 'Nguyễn Ngọc Hải',
    'sequence': '10',
    'summary': 'SCI - Onnet: Kế thừa Accounting',
    'depends': [
        'crm_his_13',
        'account',
        'account_asset_custom',
        'purchase',
        'stock'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/sh_inherit.xml',
        'views/account_asset.xml',
        'views/sale_order.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
