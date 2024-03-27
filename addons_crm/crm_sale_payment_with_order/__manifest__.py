{
    'name': 'CRM-HIS-Onnet: Tính toán tiền thực hiện dịch vụ/sản phẩm',
    'version': '1.0',
    'category': 'SCI-ONNET',
    'author': 'HaiNN',
    'sequence': '10',
    'summary': 'workflow SCI-Onnet',
    'depends': [
        'crm_his_13',
        'crm_booking_order',
        'crm_sale_payment'
    ],
    'description': '''Được cài sau khi đã cài module crm_sale_payment''',
    'data': [
        'data/paper.xml',
        'views/sale.xml',
        'views/debt.xml',
        'views/booking.xml',
        'views/template_payment.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}