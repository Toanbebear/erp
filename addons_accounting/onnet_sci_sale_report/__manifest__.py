# -*- coding: utf-8 -*-

{
    'name': 'SCI Sale Report',
    'author': 'BachTN',
    'depends': ['sale',
                'sales_team',
                'payment',
                'portal',
                'sh_intro_service',
                'utm'],
    'data': [
        # "report/sale_report_views.xml",
        "wizard/service_sale_report_detail_wizard_views.xml"
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}