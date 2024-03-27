# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'VNPAY Payment',
    'category': 'Accounting/Payment',
    'summary': 'Thanh toán qua VNPAY QR động',
    'description': """VNPAY Payment Acquirer""",
    'depends': [
        'payment',
        'sale',
        'crm_base',
        'qrcodes'
    ],
    'data': [
        'views/res_brand_view.xml',
        'views/res_company_view.xml',
        'views/res_config_settings_views.xml',
        'views/report_paperformat.xml',
        'views/report_payment_receipt_templates.xml',
        'views/account_payment_views.xml',
    ]
}
