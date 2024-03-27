# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'View His Extend',
    'version': '1.0.0',
    'summary': 'Chỉnh sửa view bệnh viện',
    'author': '',
    'category': 'Generic Modules/Medical',
    'description': ''' 
    ''',
    'depends': [
        'crm_his_13',
        'accounting_bao_cao_gia_thanh'
    ],
    'data': [
        'views/phieu_kham.xml',
        'views/phieu_xet_nghiem.xml',
        'views/phieu_chan_doan_hinh_anh.xml',
        'views/phieu_phau_thuat_thu_thuat.xml',
        'views/phieu_chuyen_khoa.xml',
        'views/benh_nhan.xml',
        'views/benh_nhan_luu.xml',
        'views/cham_soc_hau_phau.xml',
        'views/don_thuoc.xml',
        'views/phieu_tai_kham.xml',
        'views/lich_cham_soc.xml',
        'views/his_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
