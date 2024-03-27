# -*- coding: utf-8 -*-
{
    'name': "Assets Management Custom",

    'summary': """
        Assets Management Custom""",

    'description': """
        Customize Assets Management
    """,

    'author': "brianpham",
    'category': 'Accounting/Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_asset'],

    # always loaded
    'data': [
        'views/account_asset.xml',
        'views/account_asset_transfer_view.xml',
        'views/res_currency.xml'
    ],
}
