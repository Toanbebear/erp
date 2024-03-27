# -*- coding: utf-8 -*-

{
    'name': 'SCI Maintenance',
    'version': '1.0',
    'sequence': 125,
    'author': 'Chí Nguyễn',
    'company': 'Tập đoàn SCI Group',
    'website': "scigroup.com.vn",
    'depends': ['mail', 'hr', 'sci_device', 'web_timeline'],
    'data': [
        'security/maintenance.xml',
        'security/ir.model.access.csv',
        'data/maintenance_data.xml',
        'data/ir_cron_data.xml',
        'views/maintenance_views.xml',
        'views/device_main_views.xml',
        'views/equipment_export_view.xml',
        'views/hr_employee_view.xml',
        'views/website_support_templates.xml',
        'views/website_support_ticket_close_views.xml',
        'data/bien_ban_ban_giao_data.xml',
    ],
    'demo': ['data/maintenance_demo.xml'],
    'installable': True,
    'application': False,
}
