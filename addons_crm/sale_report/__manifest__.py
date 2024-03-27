{
    'name': 'Tổng hợp doanh số',
    'version': '1.0',
    'category': 'PARTNER',
    'author': 'Nguyễn Ngọc Hải',
    'sequence': '10',
    'summary': 'Gửi báo cáo doanh số hàng ngày',
    'depends': [
        'crm_sale_payment_with_order',
        'tas_payment',
        'crm_his_13'
    ],
    'data': [
        'data/ir_config_param.xml',
        'data/queue_job.xml',
        'security/group_sale_report.xml',
        'security/ir.model.access.csv',
        'views/inherit.xml',
        'views/sale_report.xml',
        'views/bc_thu_chi.xml',
        'views/menu.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
