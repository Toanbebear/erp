{
    'name': 'TAS Phiếu thu phiếu chi',
    'summary': """Phiếu thu phiếu chi """,

    'description': """
        Phiếu thu phiếu chi
    """,
    'author': "TASYS",
    'website': "",
    'category': 'tasys',
    'version': '1.0',
    'depends': ['base',  'account', 'shealth_all_in_one'],
    'images': [
        'static/description/icon.png',
    ],
    'data': [
        'views/tasys_payment_phieu_thu.xml',
        'views/tasys_payment_phieu_chi.xml',
        'views/tasys_payment_giay_bao_no.xml',
        'views/tasys_payment_giay_bao_co.xml',
        'views/tas_account_journal_form_view.xml',
        #'views/tas_account_move_line.xml',
        'views/tasys_account_payment_view.xml',
        'report/phieu_thu_chi.xml',
        'report/phieu_thu_chi_sci.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
