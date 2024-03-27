# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, time
from calendar import monthrange
from openpyxl import load_workbook
from openpyxl.styles import Font, borders, Alignment, PatternFill
import base64
from io import BytesIO
from dateutil.relativedelta import relativedelta
from operator import itemgetter

import logging

class ReportNewsHRMS(models.TransientModel):
    _name = 'report.news'
    _description = 'SCI HRMS report news'

    start_date = fields.Date('Start date', default=date.today().replace(day=1))
    end_date = fields.Date('End date')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            if self.start_date.month == fields.date.today().month:
                self.end_date = fields.date.today()
            else:
                self.end_date = date(self.start_date.year, self.start_date.month,
                                     monthrange(self.start_date.year, self.start_date.month)[1])

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        for record in self:
            start_date = fields.Date.from_string(record.start_date)
            end_date = fields.Date.from_string(record.end_date)
            if start_date > end_date:
                raise ValidationError(
                    _("End Date cannot be set before Start Date."))

    def report_news_excel(self):
        tree_view_id = self.env.ref('sci_hrms.view_report_news_tree').id
        form_view_id = self.env.ref('sci_hrms.sci_hr_applicant_view_form_inherit').id
        return {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': 'Báo cáo hiệu quả tin đăng',
            'res_model': 'hr.applicant',
            'search_view_id': self.env.ref('sci_hrms.view_report_news_filter').id,
            'domain': [('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date)],
            'context': dict(self.env.context, start_date= self.start_date, end_date=self.end_date,
                            search_default_source_id=1, search_default_job=1,  active_test=False)
        }