{
    "name": "Odoo RESTFUL API",
    "version": "1.0.1",
    "category": "API",
    "author": "Babatope Ajepe",
    "website": "https://ajepe.github.io/blog/restful-api-for-odoo",
    "summary": "Odoo RESTFUL API",
    "support": "ajepebabatope@gmail.com",
    "description": """ RESTFUL API For Odoo
====================
With use of this module user can enable REST API in any Odoo applications/modules

For detailed example of REST API refer https://ajepe.github.io/restful-api-for-odoo
""",
    "depends": ["web", "crm", "crm_base", "shealth_all_in_one", "cs_phone_3"],
    "data": [
        "data/ir_config_param.xml",
        "data/data.xml",
        "data/cron_job.xml",
        "views/ir_model.xml",
        "views/res_users.xml",
        "security/ir.model.access.csv",
        "views/crm_stage_view_inherit.xml",
        "views/custom_field_cs_views.xml",
        "views/data.xml",
        "views/mail_layout.xml",
        "views/source_view.xml",
        "views/lab_device_view.xml",
        "views/crm_lead_view_inherit.xml",
        # "views/cron_case.xml",
        "views/phone_call/config_phone_call_care_soft_views.xml",
        "views/res_brand_view.xml",
        "views/api_log.xml",
        "views/res_country_district_inherit.xml",
        "views/partner.xml",
        "views/lich_su_tham_kham.xml",
        "views/view_persona.xml",
        "views/phone_call/phonecall_view.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
}
