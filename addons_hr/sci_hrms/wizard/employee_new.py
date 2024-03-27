# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date, timedelta
from calendar import monthrange


class RecruitmentPoint(models.TransientModel):
    _name = "sci.hr.employee.new"
    _description = 'Employee new'

    date_range = fields.Selection([('this_month', 'Tháng này'), ('last_month', 'Tháng trước'), ('specific', 'Thời gian cụ thể')], string='Thời gian')
    start_date = fields.Date('Ngày bắt đầu', default=date.today().replace(day=1))
    end_date = fields.Date('Ngày kết thúc')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            if self.start_date.month == fields.date.today().month:
                self.end_date = fields.date.today()
            else:
                self.end_date = date(self.start_date.year, self.start_date.month,
                                     monthrange(self.start_date.year, self.start_date.month)[1])

    def open_report(self):
        today = date.today()
        if self.date_range != 'specific':
            if self.date_range == 'this_month':
                start_date = today.replace(day=1)
                end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])
            if self.date_range == 'last_month':
                end_date = date.today().replace(day=1) - timedelta(days=1)
                start_date = end_date.replace(day=1)
        else:
           start_date, end_date = self.start_date, self.end_date
        tree_view_id = self.env.ref('sci_hrms.view_employee_new_tree').id
        form_view_id = self.env.ref('hr.view_employee_form').id
        return {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': 'Danh sách nhân sự mới',
            'search_view_id': self.env.ref('sci_hrms.view_employee_new_filter').id,
            'res_model': 'hr.employee',
            'domain': [('joining_date', '>=', start_date), ('joining_date', '<=', end_date)],
            'context': dict(self.env.context, start_date=start_date, end_date=end_date,
                            search_default_group_hr_user_id=1, active_test=False),
        }
