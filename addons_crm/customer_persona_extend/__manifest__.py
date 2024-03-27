{
    'name': 'Customer Persona Extend',
    'version': '1.0',
    'category': 'Partner',
    'author': 'Nguyễn Ngọc Hải',
    'sequence': '10',
    'summary': 'Adding partner information to build Customer Persona',
    'depends': [
        'customer_persona',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'views/menu.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
