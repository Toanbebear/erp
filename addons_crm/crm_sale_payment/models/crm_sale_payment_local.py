import string

from odoo import api, fields, models
from odoo import fields, models, api, _
from datetime import datetime
import time
from datetime import timedelta


class CRMSalePaymentLocal(models.Model):
    _name = 'crm.sale.payment.local'
    _description = 'Số liệu cơ sở'

    name = fields.Char(string='Số liệu', readonly=True, copy=False)
    amount_proceeds = fields.Monetary(string="Số tiền giao dịch", default=0)
    update_date = fields.Date(string="Ngày cập nhật", default=fields.Date.context_today, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.company.currency_id)
    brand_id = fields.Many2one(string='Thương hiệu', comodel_name='res.brand',
                               domain=lambda self: [('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)])
    region = fields.Selection(string='Miền', selection=lambda self: self.env['res.company']._fields['zone'].selection)
    company_id = fields.Many2one(string='Chi nhánh', comodel_name='res.company',
                                 domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)], required=True)
    note = fields.Text('Ghi chú', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Xác nhận thành công')],
                             readonly=True, default='draft', copy=False, string="Status")

    @api.onchange('company_id')
    def onchange_company_id(self):
        for rec in self:
            if rec.company_id:
                rec.region = rec.company_id.zone
                rec.brand_id = rec.company_id.brand_id.id

    @api.model
    def create(self, vals):
        res = super(CRMSalePaymentLocal, self).create(vals)
        return res

    def action_confirm(self):
        if self._context.get('name', _('New')) == _('New'):
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.update_date))
            self.name = self.env['ir.sequence'].next_by_code('crm.sale.payment.local', sequence_date=seq_date) or _('New')
            self.write({'state': 'done'})

    def action_draft(self):
        self.ensure_one()
        self.name = 'New'
        self.write({'state': 'draft'})
