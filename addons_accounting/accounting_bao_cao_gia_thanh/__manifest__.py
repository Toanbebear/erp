{
    'name': 'Báo cáo giá thành',
    'summary': """Báo cáo giá thành """,

    'description': """
        Báo cáo giá thành
    """,
    'author': "TASYS",
    'website': "",
    'category': 'tasys',
    'version': '1.0',
    'depends': ['om_account_budget', 'shealth_all_in_one', 'crm_booking_share'],
    'images': [
        'static/description/icon.png',
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/mrp_bom.xml',
        'views/account_budget_view.xml',
        'views/product_cost_report_view.xml',
        'views/cost_driver_view.xml',
        'views/mrp_production.xml',
        'views/health_center.xml',
        'views/actual_cost_driver_view.xml',
        'views/plan_cost_driver_view.xml',
        'views/stock_location_view.xml',
        'views/account_account_view.xml',
        'views/account_journal_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
