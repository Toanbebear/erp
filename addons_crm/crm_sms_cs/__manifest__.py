{
    'name': 'CRM SMS Caresoft',
    'version': '1.0',
    'category': 'Sales/CRM',
    'sequence': '10',
    'summary': 'SMS Caresoft',
    'depends': [
        'crm_base',
        'shealth_all_in_one',
    ],
    'data': [
        'data/ir_cron.xml',
        'data/data.xml',
        'views/crm_sms.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
