# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
{
    'name': 'SCI HRMS',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 1,
    'summary': 'Centralize employee information',
    'author': 'Chí Nguyễn',
    'company': 'Tập đoàn SCI Group',
    'website': "scigroup.com.vn",
    'depends': ['hr', 'hr_recruitment', 'hr_contract', 'website_hr_recruitment', 'ohrms_core', 'ms_templates',
                'web_monetary_format', 'sh_message', 'sci_project', 'qrcodes'],
    'data': [
        'data/hr_data.xml',
        'data/hr_job_data.xml',
        'data/sync_user_data.xml',
        'data/mail_data.xml',
        'data/cron_get_calendar_working.xml',
        'views/hr_employee_views.xml',
        'views/hr_department_views.xml',
        'views/contract_view.xml',
        'views/hr_applicant_views.xml',
        'views/hr_resignation_view.xml',
        'views/hr_job_views.xml',
        'views/hr_project_views.xml',
        'views/templates.xml',
        'views/views_captcha.xml',
        'views/views_esms.xml',
        'views/web.xml',
        'views/salary_adjustment_notice.xml',
        'views/website_hr_recruitment_templates_new.xml',
        'views/assets_custom_css.xml',
        'views/hr_recruitment.xml',
        'wizard/recruitment_point.xml',
        'wizard/max_emp_report.xml',
        'wizard/employee_new.xml',
        'wizard/employee_checklist.xml',
        'wizard/report_news.xml',
        'wizard/sms_wizard.xml',
        'security/ir.model.access.csv',
        'security/group.xml',
        'views/sync_user.xml',
        # #report
        'wizard/report_applicant.xml',
        'wizard/employee_quit.xml',
        'data/report_applicant.xml',
        #
        # #contract
        'data/contract/SCI/hr_contract_attachment_sci.xml',
        'data/contract/paris/hr_contract_attachment_paris.xml',
        'data/contract/kangnam/hr_contract_attachment_kn.xml',
        'data/contract/hongha/hr_contract_attachment_hh.xml',
        'data/contract/donga/hr_contract_attachment_da.xml',
        'data/contract/academy/hr_contract_attachment_hv.xml',
        # 'data/contract/SCI/hr_data_contract_sci.xml',
        # 'data/contract/academy/hr_data_contract_academy.xml',
        # 'data/contract/kangnam/hr_data_contract_kangnam.xml',
        # 'data/contract/hongha/hr_data_contract_hongha.xml',
        # 'data/contract/donga/hr_data_contract_donga.xml',
        # 'data/contract/paris/hr_data_contract_paris.xml',
        # 'data/contract/paris/hr_data_trial_contract_paris.xml',
        # 'data/contract/paris/hr_data_official_contract_paris.xml',

    ],
    'qweb': [
        'static/src/xml/view.xml'
    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
###################################################################################
