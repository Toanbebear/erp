# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Chỉnh sửa hiển thị CRM',
    'version': '1.1',
    'summary': 'Thêm thông tin giá bán dịch vụ vào form view của CRM Line',
    'author': 'hungtn@scigroup.com.vn',
    'category': 'Sales/CRM',
    'description': ''' 
        Tại form view chọn dịch vụ add vào crm line, 
        người dùng chọn dịch vụ từ bảng giá chi tiết, có hiển thị theo cấu trúc [Mã dịch vụ] - [Tên dịch vụ] - [Giá dịch vụ]
    ''',
    'depends': [
        'crm_his_13',
    ],
    'data': [
        'views/view_crm_line_inherit.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
