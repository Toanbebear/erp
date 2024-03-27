# -*- coding: utf-8 -*-
{
    'name': 'Accounting Asset',
    'author': 'NghiaNT',
    'description': """Export account asset report in excel format""",
    'summary': 'Export account asset',
    'category': 'Accounting/Accounting',
    'depends': ['account', 'account_asset_custom', 'custom_partner'],
    'data': [
        'wizard/account_asset_report_wizard.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': "LGPL-3",
}
