{
    'name': 'Thuê phòng mổ',
    'version': '1.0',
    'category': 'Sales/CRM',
    'author': '',
    'sequence': '1',
    'summary': 'Xử lý case thuê phòng mổ SCI',
    'depends': [
        'crm_his_13',
        'crm_sale_payment_with_order'
    ],
    'data': [
        # 'views/product_template_vỉew.xml',
        # 'views/product_product_vỉew.xml',
        'data/product.xml',
        'views/crm_lead_view.xml',
        'views/stock.xml',
        'wizard/create_walkin_share.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
