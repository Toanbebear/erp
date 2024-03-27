# -*- coding: utf-8 -*-

import time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, time
from calendar import monthrange

class AccountDebtReport(models.TransientModel):
    _name = 'account.debt.report'
    _description = 'Account Receivable/Payable Report'

    report_type = fields.Selection(
        [('Receivable', 'BC công nợ phải thu'), ('Payable', 'BC công nợ phải trả')],
        string='Loại báo cáo', default='Receivable')

    start_date = fields.Date('Từ ngày', default=date.today().replace(day=1))
    end_date = fields.Date('Đến ngày')

    account_id = fields.Many2many('account.account', string='Tài khoản')

    @api.onchange('report_type')
    def _change_report_type(self):
        domain = {'domain': {}}
        if self.report_type == 'Receivable':
            domain['domain']['account_id'] = ['|',('name', 'ilike', '131'),('name', 'ilike', '136'),
                                               ('company_id', 'in', self.env.companies.ids)]
            data_account = self.env['account.account'].search(['|',('name', 'ilike', '131'),('name', 'ilike', '136'),
                                               ('company_id', 'in', self.env.companies.ids)])
            self.account_id = [(6,0,data_account.ids)]
        elif self.medicament_type == 'Payable':
            domain['domain']['account_id'] = ['|', ('name', 'ilike', '331'), ('name', 'ilike', '336'),
                                              ('company_id', 'in', self.env.companies.ids)]
            data_account = self.env['account.account'].search(['|', ('name', 'ilike', '331'), ('name', 'ilike', '336'),
                                                               ('company_id', 'in', self.env.companies.ids)])
            self.account_id = [(6, 0, data_account.ids)]
        return domain

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

    def print_account_debt_report(self):
        template = self.env.ref('accounting_xls_reports.bao_cao_cong_no')
        start_date = self.start_date
        end_date = self.end_date
        # if start_date.month != end_date.month:
        #     raise UserError(_('Nhập ngày bắt đầu và kết thúc trong cùng một tháng'))
        # if start_date.day != 1:
        #     raise UserError(_('Nhập ngày bắt đầu là mùng 1'))

        account_text = ','.join(self.account_id.name)
        if self.report_type == 'Receivable':
            account_move_lines = self.env['account.move.line'].search([('company_id', 'in', self.env.companies.ids),
                      '|',('account_id.name','ilike','131'),('account_id.name','ilike','136'),
                      ('date', '>=', start_date),('date', '<=', end_date)])
        else:
            account_move_lines = self.env['account.move.line'].search([('company_id', 'in', self.env.companies.ids),
                                                                       '|', ('account_id.name', 'ilike', '331'),
                                                                       ('account_id.name', 'ilike', '336'),
                                                                       ('date', '>=', start_date),
                                                                       ('date', '<=', end_date)])

        external_keys = {'a1': 'CHI TIẾT CÔNG NỢ PHẢI THU' if self.report_type == 'Receivable' else 'CHI TIẾT CÔNG NỢ PHẢI TRẢ',
                         'a2': 'Tài khoản: %s' % account_text,
                         'a3': 'Từ %s đến %s' % (start_date.strftime('%d/%m/%Y'), end_date.strftime('%d/%m/%Y'))}

        return {'name': (_('Báo cáo công nợ')),
                'type': 'ir.actions.act_window',
                'res_model': 'temp.wizard',
                'view_mode': 'form',
                'target': 'inline',
                'view_id': self.env.ref('ms_templates.report_wizard').id,
                'context': {'default_template_id': template.id, 'active_ids': account_move_lines.ids,
                            'external_keys': external_keys,
                            'active_model': 'account.move.line'}}

