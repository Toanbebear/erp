# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo 13 Accounting EXCEL Reports',
    'version': '13.0.1.1.2',
    'category': 'Invoicing Management',
    'summary': 'Accounting Reports For Odoo 13',
    'sequence': '10',
    'author': 'SCI GROUP, DUNG NTP',
    'license': 'LGPL-3',
    'company': 'SCI GROUP',
    'depends': ['account','ms_templates'],
    'demo': [],
    'data': [
        'data/template_attachment.xml',
        'views/report_templates.xml',
        'views/account_xls_reports.xml',
        'wizards/account_debt.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/icon.png'],
    'qweb': [],
}
