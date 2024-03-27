{
    'name': 'Custom Partner Evaluation',
    'version': '1.0',
    'author': 'Dungntp',
    'sequence': '10',
    'summary': 'Cập nhật thêm tab phiếu tái khám vào partner',
    'depends': [
        'shealth_all_in_one',
        'crm_phone_call'
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
