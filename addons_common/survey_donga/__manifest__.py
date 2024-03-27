# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Surveys Đông Á',
    'version': '3.0',
    'category': 'Marketing',
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
    'website': 'https://www.odoo.com/page/survey',
    'depends': ['survey_base', 'sci_brand'],
    'data': [
        'views/survey_template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 5,
}
