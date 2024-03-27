# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'View ERP Kangnam',
    'version': '1.0.0',
    'summary': 'Chỉnh view cho Kangnam',
    'author': '',
    'category': 'CRM',
    'description': ''' 
        Các màn hình:
            1. Lễ tân:
                - Màn booking
                
    ''',
    'depends': [
        'crm_his_13',
        'crm_booking_share',
        'payment_schedule'
    ],
    'data': [
        'security/security.xml',
        'views/crm_kangnam_crm_lead_view.xml',
        'views/crm_kangnam_menus.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
