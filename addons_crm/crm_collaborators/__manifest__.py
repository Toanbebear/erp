{
    'name': 'CỘNG TÁC VIÊN HỒNG HÀ',
    'version': '1.0',
    'category': 'Sales/CRM',
    'sequence': '12',
    'author': 'ToanBebear',
    'summary': 'CTV',
    'depends': [
        # 'crm',
        'crm_his_13',
        # 'crm_base',
        # 'sci_brand',
        'account',
        'qrcodes',
    ],
    'data': [
        'security/security_collaborators.xml',
        'security/ir.model.access.csv',
        # 'data/cron_update_collaborators.xml',
        # 'data/account_data.xml',
        # 'views/inherit_account_payment_collaborators_views.xml',
        'views/collaborators_views.xml',
        # 'views/products_discount_views.xml',
        # 'views/collaborators_contract_views.xml',
        # 'views/crm_payment_ctv_views.xml',
        # 'views/view_account_payment_collaborators.xml',
        # 'wizard/check_partner.xml',
        # 'wizard/cancel_contract_view.xml',
        # 'wizard/bao_cao_chi_tiet_doanh_so/collaborator_report.xml',
        # 'wizard/bao_cao_hoa_hong_cong_tac_vien/collaborator_payment_view_report.xml',
        'views/menu_collaborators_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}