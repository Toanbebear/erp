# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys (<https://www.cybrosys.com>)
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
###################################################################################
{
    'name': 'Open HRMS Core',
    'version': '13.0.1.1.0',
    'summary': """Open HRMS Suit: It brings all Open HRMS modules""",
    'description': """Main module of Open HRMS, It brings all others into a single module, Payroll, Payroll Accounting,Expense,
                Dashboard, Employees, Employee Document, Resignation, Salary Advance, Loan Management, Gratuity, Service Request, Gosi, WPS Report, Reminder, Multi Company, Shift Management, Employee History,
                Branch Transfer, Employee Appraisal,Biometric Device, Announcements, Insurance Management, Vacation Management,Employee Appreciations, Asset Custody, Employee Checklist, Entry and Exit Checklist, Disciplinary Actions, Attrition Rate, Document Expiry, Visa Expiry, Law Suit Management, Employee, Employee Training""",
    'category': 'Human Resources',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'live_test_url': 'http://demo.openhrms.com/web/signup',
    'website': "https://www.openhrms.com",
    'depends': ['hr',
                'hr_employee_updation',
                'hr_recruitment',
                'oh_employee_check_list',
                'hr_reward_warning',
                'hrms_dashboard',
                'hr_resignation',
                'to_attendance_device',
                'om_hr_payroll_account',
                # 'om_account_accountant',
                'hr_multi_company',
                'hr_disciplinary_tracking',
                # 'hr_insurance',
                'hr_skills',
                'backend_theme_v13'
                ],
    'data': [
        'views/menu_arrangement_view.xml',
        'views/hr_config_view.xml',
	    'views/template_view.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.gif'],
    'qweb': ["static/src/xml/link_view.xml"],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
