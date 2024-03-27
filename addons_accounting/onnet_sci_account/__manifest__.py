# -*- coding: utf-8 -*-

{
    'name': 'Onnet SCI Accounting Customizations',
    'author': 'Onnet',
    'depends': ['sci_payment_list',
                'accounting_pdf_reports',
                ],
    'data': [
        'data/account_data.xml',
        'views/account_payment_views.xml',
        'wizards/partner_ledger.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
