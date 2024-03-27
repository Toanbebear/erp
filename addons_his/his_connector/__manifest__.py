{
    'name': 'Sync His 83',
    'version': '1.0',
    'sequence': 7,
    'author': "NamAhihi",
    'summary': 'Đồng bộ dữ liệu sang 83 tiêu chí',
    'depends': ['base', 'crm_base', 'crm_sms_cs'],
    'support': '',
    'description': """""",
    "website": "http://scigroup.com.vn/",
    "data": [
        'security/security.xml',
        'views/inherit_res_company_view.xml',
        'views/inherit_crm_lead.xml',

        'wizard/sync_his_83_wizard.xml',
    ],
    'application': True,
    "active": True
}
