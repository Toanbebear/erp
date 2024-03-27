# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Booking Bảo hành',
    'version': '1.0.1',
    'summary': 'Làm những thứ liên quan đến booking bảo hành',
    'author': '',
    'category': 'CRM',
    'description': ''' 
    ''',
    'depends': [
        'crm_his_13'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_guarantee_reason.xml',
        'views/crm_line.xml',
        'views/sh_medical_appointment_register_walkin.xml',
        'wizard/crm_create_guarantee.xml',
        'wizard/add_service_guarantee.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
