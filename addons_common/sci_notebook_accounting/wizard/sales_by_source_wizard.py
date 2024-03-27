from odoo import fields, models, api, _
from datetime import date, datetime, time
from pytz import timezone, utc
from calendar import monthrange
from odoo.exceptions import ValidationError, UserError


class SaleBySourceWizard(models.TransientModel):
    _name = 'sales.by.source.wizard'
    _description = 'Description'

    start_date = fields.Date(string='Từ ngày', required=True)
    end_date = fields.Date(string='Đến ngày', required=True)
    # sale_by_source_ids = fields.Many2many(comodel_name='sales.by.source')
    company_ids = fields.Many2many(comodel_name='res.company', string='Công ty', domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)])

    # convert date to datetime for search domain, should be removed if using datetime directly
    start_datetime = fields.Datetime('Start datetime', compute='_compute_datetime')
    end_datetime = fields.Datetime('End datetime', compute='_compute_datetime')

    @api.depends('start_date', 'end_date')
    def _compute_datetime(self):
        self.start_datetime = False
        self.end_datetime = False
        if self.start_date and self.end_date:
            local_tz = timezone(self.env.user.tz or 'Etc/GMT+7')
            start_datetime = datetime(self.start_date.year, self.start_date.month, self.start_date.day, 0, 0, 0)
            end_datetime = datetime(self.end_date.year, self.end_date.month, self.end_date.day, 23, 59, 59)
            start_datetime = local_tz.localize(start_datetime, is_dst=None)
            end_datetime = local_tz.localize(end_datetime, is_dst=None)
            self.start_datetime = start_datetime.astimezone(utc).replace(tzinfo=None)
            self.end_datetime = end_datetime.astimezone(utc).replace(tzinfo=None)

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
            days = (end_date - start_date).days
            if days < 0:
                raise ValidationError(
                    _("Ngày kết thúc không thể ở trước ngày bắt đầu khi xuất báo cáo!!!"))

    def request_locked(self):
        data = self.env['sales.by.source'].search([('date', '>=', self.start_datetime),
                                                   ('date', '<=', self.end_datetime),
                                                   ('company_id', 'in', self.company_ids.ids)])
        for rec in data:
            if rec.state == 'posted':
                rec.write({'state': 'locked'})

    def request_unlocked(self):
        data = self.env['sales.by.source'].search([('date', '>=', self.start_datetime),
                                                   ('date', '<=', self.end_datetime),
                                                   ('company_id', 'in', self.company_ids.ids)])
        for rec in data:
            if rec.state == 'locked':
                rec.write({'state': 'posted'})