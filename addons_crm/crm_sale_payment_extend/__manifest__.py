{
    'name': 'CRM Sale Payment Extend',
    'version': '1.0.0',
    'category': 'Sales/CRM',
    'author': 'NamDZ',
    'sequence': '11',
    'summary': 'Sale Payment',
    'depends': [
        'crm_sale_payment'
    ],
    'data': [
        'views/crm_sale_payment_plan.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
