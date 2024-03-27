# -*- coding: utf-8 -*-
{
    'name': 'BẢNG KÊ THANH TOÁN',
    'version': '1.0',
    'category': 'SCI',
    'sequence': 1,
    'description': """
    Lập bảng kê, có nhiều loại thanh toán
    =====================================


    * Dữ liệu phòng ban
    * Dữ liệu vị trí công việc
    * Dữ liệu nhân viên
    * Dữ liệu người dùng

    """,
    'company': 'Tập đoàn SCI Group',
    'website': "scigroup.com.vn",
    'depends': ['account', 'sci_brand', 'hr', 'crm_base', 'shealth_all_in_one'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir.rule.xml',
        'data/payment_list_sequence.xml',
        'views/payment_list_view.xml',
        'views/account_payment.xml',
        'views/print_payment_list.xml',
        'report/report.xml'
    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}