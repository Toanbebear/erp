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

class ReportApplicantHRMS(models.TransientModel):
    _name = 'report.applicant'
    _description = 'SCI HRMS report applicant'

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
            if not start_date and not end_date:
                raise ValidationError("Ngày báo cáo không được để trống!!!")
            if start_date > end_date:
                raise ValidationError(
                    _("End Date cannot be set before Start Date."))

    def report_applicant_excel(self):
        template = self.env.ref('sci_hrms.report_applicant_template')
        domain_applicant = [('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date), ]
        list_applicant = self.env['hr.applicant'].search(domain_applicant)
        return {'name': (_('report_applicant')),
                'type': 'ir.actions.act_window',
                'res_model': 'temp.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'inline',
                'view_id': self.env.ref('ms_templates.report_wizard').id,
                'context': {'default_template_id': template.id, 'active_ids': list_applicant.ids,
                            'active_model': 'hr.applicant',
                            'external_keys': {
                                'h3': self.start_date.strftime('%d/%m/%Y'),
                                'k3': self.end_date.strftime('%d/%m/%Y'),
                                'p1503': date.today().strftime(' %d/%m/%Y'),
                                'p1509':self.env.user.name,
                            }}}