{
    'name': 'Chương trình Voucher',
    'version': '1.0',
    'category': 'Sales/CRM',
    'author': '',
    'sequence': '10',
    'summary': 'apply voucher to lead/booking',
    'depends': [
        'crm_his_13',
        'crm_booking_order',
        'qrcodes'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        # 'data/data_default.xml',
        'views/crm_voucher_program_view.xml',
        'views/crm_voucher.xml',
        'views/inherit.xml',
        'wizard/apply_voucher.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
        # 'static/src/xml/button_tree.xml'
    ],
}
