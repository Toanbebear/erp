{
    'name': 'SH Phiếu khám',
    'version': '13.0.1.0',
    'category': 'Generic Modules/Medical',
    'sequence': 2,
    'summary': 'Phiếu khám',
    'website': '',
    'depends': ['shealth_all_in_one'],
    'description': """""",
    'data': [
        'views/js_temp.xml',
        'views/phieu_kham.xml',
        'views/phieu_xet_nghiem.xml',
        'views/phieu_chan_doan_ha.xml',
        'views/phieu_phau_thuat_thu_thuat.xml',
        'views/phieu_chuyen_khoa.xml',
        'views/phieu_benh_nhan_luu.xml',
        'views/phieu_lich_tai_kham.xml',
        'views/inherit_walkin.xml'
    ],
    'demo': [],
    'application': True,
    'license': 'OEEL-1',
    'qweb': [
        'static/xml/button_tree_reset_lab_test.xml',
        'static/xml/button_tree_add_lab_test.xml',
    ],
}
