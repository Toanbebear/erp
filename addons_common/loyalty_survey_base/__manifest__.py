# -*- encoding: utf-8 -*-
{
    'name': 'Surveys Loyalty base',
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
    'depends': ['website', 'web', 'crm_base', 'loyalty', 'base'],
    'data': [
        # 'security/base_security.xml',
        'views/loyalty_card_views.xml',
        'views/crm_brand_inherit.xml',
        'views/res_company_inherit.xml',


    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 5,
}
