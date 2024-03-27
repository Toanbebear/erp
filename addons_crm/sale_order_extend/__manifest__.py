{
    'name': 'Lịch sử trả nợ',
    'version': '1.0.0',
    'category': 'Sales',
    'sequence': '3',
    'author': 'NamDZ',
    'summary': 'Lịch sử trả nợ',
    'depends': [
        'sale', 'crm_his_13', 'collaborator'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/crm_debt_review.xml',
        'wizard/crm_debt_warning.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
