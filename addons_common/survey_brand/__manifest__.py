# -*- encoding: utf-8 -*-
{
    'name': 'Surveys Brand',
    'version': '3.0',
    'category': 'Marketing/Survey',
    'description': """
        Tạo khảo sát cho các thương hiệu
    """,
    'summary': 'Create surveys and analyze answers',
    'depends': ['survey', 'website', 'web', 'crm_base', 'sci_brand', 'survey_base', 'link_tracker'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_config_param.xml',
        'data/cron_job_survey_sms.xml',
        # 'data/survey_survey_type.xml',
        'data/cron_job_user_input.xml',
        'wizard/survey_user_input_report_wizard_view.xml',
        'wizard/survey_user_input_da_report_wizard_view.xml',
        'views/survey_question_views.xml',
        # 'views/survey_template.xml',
        'views/survey_user_input.xml',
        'views/survey_survey.xml',
        'views/survey_template.xml',
        'views/crm_lead_view.xml',
        'views/res_partner_views.xml',
        # 'views/res_brand_view.xml',
        'views/evaluation_view.xml',
        'views/walkin_view.xml',
        'views/survey_survey_type.xml',
        'views/survey_brand_config_views.xml',
        'views/survey_survey_rule_sms.xml',
        'views/menu_action.xml',
        'views/phone_call_view.xml',
        'views/survey_send_mail_sms.xml',
        # 'report/paperformat.xml',
        # 'report/template.xml',
        # 'report/report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 5,
}
