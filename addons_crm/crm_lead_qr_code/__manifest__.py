{
    'name': 'CRM QR CODE',
    'version': '1.0',
    'category': 'Sales/CRM',
    'author': 'Nguyễn Hữu Toàn',
    'depends': [
        'crm_base',
        'qrcodes',
    ],
    'data': [
        'views/crm_lead_inherit_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
