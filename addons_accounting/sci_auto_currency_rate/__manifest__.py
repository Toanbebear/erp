# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Sci Auto Currency Rate',
    'version': '1.0',
    'sequence': 160,
    'category': 'Accounting/Accounting',
    'depends': ['base'],
    'description': """
        Tự động lấy tỉ giá tiền tệ
    """,

    'data': [
        'data/cron.xml',
        'views/res_currency_views.xml',
    ],
}
