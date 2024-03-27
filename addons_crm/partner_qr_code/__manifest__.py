{
    'name': 'PARTNER QR CODE',
    'version': '1.0',
    'category': 'Sales/CRM',
    'author': 'Nguyễn Hữu Toàn',
    'depends': [
        'crm_base',
        'qrcodes',
    ],
    'data': [
        'views/partner_inherit_qr_code_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
