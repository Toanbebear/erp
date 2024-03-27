{
    'name': 'CRM Phone call',
    'version': '1.0',
    'category': 'Sales/CRM',
    'sequence': '10',
    'summary': 'CRM Phone call',
    'depends': [
        'crm_base',
        'shealth_all_in_one',
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/crm_phone_call_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
