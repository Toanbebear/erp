{
    'name': 'Kết nối Zalo ZNS CS',
    'version': '1.0',
    'category': 'Sales/CRM',
    'sequence': '10',
    'summary': 'CRM Zalo ZNS',
    'depends': ["crm_sms_cs", "base", "loyalty"],
    'data': [
        'data/data.xml',

        'views/script_sms.xml',
        'views/crm_sms.xml',
        'views/loyalty_rank.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
