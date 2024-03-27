{
    'name': 'Voucher accesstrade',
    'version': '1.0.0',
    'category': 'Sales',
    'sequence': '3',
    'author': 'NamDZ',
    'summary': 'Lưu trữ voucher accesstrade',
    'depends': [
        'crm_voucher', 'queue_job'
    ],
    'data': [
        'data/ir_config_param.xml',
        'data/data.xml',
        'views/crm_voucher_program.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
