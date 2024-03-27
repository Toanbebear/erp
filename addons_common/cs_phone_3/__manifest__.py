# -*- coding: utf-8 -*-

{
    "name": "CS Phone 3",
    "summary": "Thêm số điện thoại thứ 3",
    "version": "13.0.0.1",
    "category": "Sales/CRM",
    'sequence': 2,
    "website": "https://caresoft.vn",
    "description": """
		Thêm số điện thoại thứ 3
    """,
    "author": "Z",
    "license": "LGPL-3",
    "installable": True,
    'application': True,
    "depends": [
        'crm_base',
    ],
    "data": [
        'views/crm_lead_inherit_view.xml',
        'views/res_partner_inherit_view.xml'
    ],
}
