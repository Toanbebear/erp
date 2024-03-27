# -*- coding: utf-8 -*-

{
    "name": "Mở rộng ích hợp tổng đài Caresoft",
    "summary": "Mở rộng tích hợp tổng đài Caresoft với CRM",
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
        'sci_brand',
        'call_center_cs'
    ],
    "data": [
        'views/res_brand_view.xml'
    ],
}

