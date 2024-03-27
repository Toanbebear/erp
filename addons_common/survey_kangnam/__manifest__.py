# -*- encoding: utf-8 -*-
{
    'name': 'Surveys Kangnam',
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
    'summary': 'Create survey and analysis answers for Kangnam Beauty Hospital',
    'depends': ['survey_base', 'shealth_all_in_one'],
    'data': [
        'views/inherit_walkin.xml',
        'views/inherit_survey.xml',
        # 'views/template_survey_web.xml',
        'views/inherit_survey_question.xml',
        'views/survey_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 5,
}
