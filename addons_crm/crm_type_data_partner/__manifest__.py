{
    'name': 'Phân loại khách hàng cũ mới',
    'version': '1.0',
    'category': 'PARTNER',
    'author': 'Nguyễn Ngọc Hải',
    'sequence': '10',
    'summary': 'Thêm tính năng phân loại khách hàng cũ/mới dựa vào thông tin khách hàng đã từng sử dụng dịch vụ tại SCI',
    'depends': [
        'custom_partner',
        'crm_base'
    ],
    'data': [
        'view/view_partner.xml',
        'view/crm_lead.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
