# -*- coding: utf-8 -*-
{
    'name': 'Print Partner Code',
    'version': '13.0.1.0.1',
    'category': 'CRM',
    'author': 'SCI-IT',
    'website': "",
    'license': 'LGPL-3',
    'summary': """In QR Code của khách hàng""",
    'images': ['static/description/icon.png'],
    'description': """

    """,
    'depends': ['base'],
    'data': [
        'data/ir_config_parameter.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/asset.xml',
        'wizard/print_partner_code_views.xml',
        'report/partner_code_reports.xml',
        'report/partner_code_templates.xml',
    ],
    'qweb': [
        'static/src/xml/view.xml',
    ],
    'support': '',
    'application': False,
    'installable': True,
    'auto_install': False,
}
