# -*- coding: utf-8 -*-  

{
    'name': 'SCI Device Management',
    'description': 'Device Management',
    'summary': 'Device Management',
    'category': 'Construction',
    "sequence": 3,
    'version': '1.0.0',
    'author': 'SCI-IT',
    'company': 'Tập đoàn SCI Group',
    'website': "scigroup.com.vn",
    'depends': [
        'sci_hrms',
        'qrcodes',
    ],
    'data': [
        'views/device/device_extra.xml',
        'views/device/device_main.xml',
        'views/device/device_parts_in.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'menu/device_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
