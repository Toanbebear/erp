# -*- coding: utf-8 -*-

{
    "name": "Tích hợp tổng đài Caresoft",
    "summary": "Tích hợp tổng đài Caresoft với CRM",
    "version": "13.0.0.1",
    "category": "Sales/CRM",
    'sequence': 2,
    "website": "https://caresoft.vn/",
	"description": """
		Tích hợp tổng đài Caresoft cho phép gọi điện cho khách hàng
    """,
    "author": "thond",
    "license": "LGPL-3",
    "installable": True,
    'application': True,
    "depends": [
        'web',
        'hr',
        'sci_brand',
        'crm_base'
    ],
    "data": [
        'views/assets.xml',
        'views/res_brand_view.xml',
        'views/res_users.xml',
        'views/cs_setting_views.xml',
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/crm_phone_call.xml",
        "views/brand_ip_phone_view.xml"
    ],
}

