{
    'name': 'Lịch trình thanh toán',
    'version': '1.0',
    'category': 'CRM',
    'author': 'Nguyễn Ngọc Hải',
    'sequence': '10',
    'summary': '',
    'depends': [
        'crm_his_13'
    ],
    'data': [
        'views/assets.xml',
        'views/crm_lead.xml',
        'wizard/payment_schedule.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
