{
    'name': 'Kết nối chân dung khách hàng',
    'version': '1.0',
    'category': 'PARTNER',
    'author': 'Nguyễn Ngọc Hải',
    'sequence': '1',
    'summary': '',
    'depends': [
        'customer_persona_extend', 'crm_his_13', 'crm_booking_order'
    ],
    'data': [
        'data/parameter_config.xml',
        'view/view_persona.xml',
        'view/lich_su_tham_kham.xml',
        'view/crm_lead.xml',
        'view/partner.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
