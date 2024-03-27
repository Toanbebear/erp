# -*- coding: utf-8 -*-
{
    'name': 'Product Pricelist New',
    'version': '13.0.1.0.0',
    'category': 'CRM',
    'author': 'NamDZ',
    'website': "",
    'license': 'LGPL-3',
    'summary': """Bảng giá mới
    """,
    'images': ['static/description/icon.png'],
    'description': """

    """,
    'depends': ['crm_kangnam_extend'],
    'data': [
        'views/product_pricelist.xml',
        'views/crm_lead.xml',
        'views/sale_order_line.xml',
        'views/crm_line.xml',
        'views/crm_phone_call.xml',
        'views/crm_voucher.xml',
        'wizard/crm_cancel_voucher.xml',
        'wizard/apply_voucher.xml',
    ],
    'qweb': [
    ],
    'support': '',
    'application': False,
    'installable': True,
    'auto_install': False,
}
