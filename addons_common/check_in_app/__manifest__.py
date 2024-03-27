# -*- coding: utf-8 -*-

{
    "name": "Check In App",
    "summary": "Ứng dụng hỗ trợ khách hàng checkin tại chi nhánh",
    "version": "0.0.1",
    "category": "CRM",
    'sequence': 2,
    "author": "IT SCI",
    "license": "LGPL-3",
    "installable": True,
    'application': True,
    "depends": [
        'crm_base',
        'restful',
        'collaborator'
    ],
    "data": [
        'data/paper.xml',
        'data/data_default.xml',
        'views/asset.xml',
        'security/ir.model.access.csv',
        'security/rule.xml',
        'views/crm_check_in_views.xml',
        'views/crm_ctv_check_in_views.xml',
        'views/crm_event_check_in_views.xml',
        'views/crm_check_in_service_category.xml',
        'views/phieu_thong_tin_khach_hang.xml',
        'views/crm_check_in_otp_views.xml',
        'views/template_kn.xml',
        'views/template_pr.xml',
        'views/menu.xml',
        'wizard/create_booking.xml',
    ],
    'qweb': [
        'static/src/xml/attendance.xml',
    ],
}

