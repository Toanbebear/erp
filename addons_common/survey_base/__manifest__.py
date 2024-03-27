# -*- encoding: utf-8 -*-
{
    'name': 'Surveys Base',
    'version': '3.0',
    'category': 'Marketing/Survey',
    'description': """
Create beautiful surveys and visualize answers
==============================================

It depends on the answers or reviews of some questions by different users. A
survey may have multiple pages. Each page may contain multiple questions and
each question may have multiple answers. Different users may give different
answers of question and according to that survey is done. Partners are also
sent mails with personal token for the invitation of the survey.
    """,
    'summary': 'Create surveys and analyze answers',
    'depends': ['survey', 'website', 'web', 'crm_base', 'sci_brand'],
    'data': [
        'security/base_security.xml',
        'views/survey_question_views.xml',
        'views/survey_template.xml',
        'views/survey_survey.xml',
        'views/survey_template.xml',
        'views/crm_lead_inherit_view.xml',
        'views/menu_action.xml',
        'report/paperformat.xml',
        'report/template.xml',
        'report/report.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 5,
}
