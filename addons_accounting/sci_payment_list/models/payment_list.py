from odoo import fields, models, api, _
from lxml import etree
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError
import json
# def num2words_vnm(num):
#     num = int(num)
#     under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
#                 'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
#     tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
#     above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}
#
#     if num < 20:
#         return under_20[num]
#
#     elif num < 100:
#         under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
#         result = tens[num // 10 - 2]
#         if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
#             result += ' ' + under_20[num % 10]
#         return result
#
#     else:
#         unit = max([key for key in above_100.keys() if key <= num])
#         result = num2words_vnm(num // unit) + ' ' + above_100[unit]
#         if num % unit != 0:
#             if num > 1000 and num % unit < unit / 10:
#                 result += ' không trăm'
#             if 1 < num % unit < 10:
#                 result += ' linh'
#             result += ' ' + num2words_vnm(num % unit)
#     return result.capitalize()

class PaymentList(models.Model):
    _name = 'payment.list'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'money.mixin']
    _description = 'Bảng kê thanh toán'

    name = fields.Char(string='Số chứng từ', readonly=True, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Chờ xác nhận'), ('done', 'Xác nhận thành công'), ('cancelled', 'Cancelled')],
                             readonly=True, default='draft', copy=False, string="Status")
    payment_type = fields.Selection([('outbound', 'Phiếu chi'), ('inbound', 'Phiếu thu')],
                                    string='Loại thanh toán', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    payment_method = fields.Many2one('account.payment.method', string='Phương thức', compute='_get_payment_method', store=True, tracking=True)
    partner_type = fields.Selection([('customer', 'Khách hàng'), ('supplier', 'Nhà cung cấp')], required=True,
                                    string='Loại đối tác', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Khách hàng', tracking=True, readonly=True, required=True, states={'draft': [('readonly', False)]},
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', string='Công ty', required=True, default=lambda self: self.env.company, readonly=True)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True)
    payment_date = fields.Date(string='Date', default=fields.Date.context_today, required=True, readonly=True,
                               states={'draft': [('readonly', False)]}, copy=False, tracking=True)
    communication = fields.Char(string='Nội dung thanh toán', readonly=True, required=True, states={'draft': [('readonly', False)]})
    crm_id = fields.Many2one('crm.lead', string='Booking/lead', domain="[('partner_id','=', partner_id), ('type', '=', 'opportunity')]", tracking=True)

    def get_domain_user(self):
        thungan_job = self.env['hr.job'].sudo().search([('name', 'ilike', 'thu ngân'), ('company_id', 'in', self.env.companies.ids)])

        emp_user = self.env['hr.employee'].sudo().search([('job_id', 'in', thungan_job.ids),
                                                          ('company_id', 'in', self.env.companies.ids), ('user_id', '!=', False)])

        if thungan_job and emp_user:
            return [("groups_id", "in", [self.env.ref("account.group_account_invoice").id]),
                    ('company_id', '=', self.env.companies.ids), ('id', 'in', emp_user.sudo().mapped('user_id').ids)]
        else:
            return [("groups_id", "in", [self.env.ref("account.group_account_invoice").id]),
                    ('company_id', '=', self.env.companies.ids)]

    user = fields.Many2one('res.users', string='Người thu', domain=lambda self: self.get_domain_user(),
                           default=lambda self: self.env.user if self.env.user.has_group(
                               "shealth_all_in_one.group_sh_medical_accountant") else False, tracking=True)
    payment_ids = fields.One2many('account.payment', 'payment_list_id', string='Phiếu thanh toán', tracking=True, states={'draft': [('readonly', False)]})
    amount_subtotal = fields.Monetary(string='Tổng tiền bảng kê', compute='_get_amount_subtotal')
    currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ', required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env.company.currency_id.id)

    @api.depends('payment_type')
    def _get_payment_method(self):
        for rec in self:
            if rec.payment_type == 'inbound':
                domain = [('payment_type', '=', 'inbound')]
            else:
                domain = [('payment_type', '=', 'outbound')]
            rec.payment_method = self.env['account.payment.method'].search(domain, limit=1)

    def action_confirm(self):
        if self._context.get('name', _('New')) == _('New'):
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.payment_date))
            self.name = self.env['ir.sequence'].next_by_code('payment.list', sequence_date=seq_date) or _('New')
            self.write({'state': 'waiting'})
            for pay in self.payment_ids:
                pay.write({
                    'payment_list_state': 'waiting'
                })

    def action_draft(self):
        self.ensure_one()
        if any(pay.state in ('posted',) for pay in self.payment_ids):
            raise UserError(
                _('Đã có phiếu thu ở được xác nhận. Bạn không thể thực hiện hành động này'))
        self.name = 'New'
        self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        if vals.get('payment_ids'):
            payment_ids = vals['payment_ids']
            for pay in payment_ids:
                pay[2]['payment_list_state'] = 'draft'
                pay[2]['payment_date'] = vals.get('payment_date', None)
                if vals['payment_type'] == 'inbound':
                    domain = [('payment_type', '=', 'inbound')]
                else:
                    domain = [('payment_type', '=', 'outbound')]
                pay[2]['payment_method_id'] = self.env['account.payment.method'].search(domain, limit=1).id
            res = super(PaymentList, self).create(vals)
            for pay in res.payment_ids:
                pay.payment_type = pay.payment_list_id.payment_type

                pay.partner_type = pay.payment_list_id.partner_type
                pay.partner_id = pay.payment_list_id.partner_id

                pay.crm_id = pay.payment_list_id.crm_id
                pay.communication = pay.payment_list_id.communication
        else:
            res = super(PaymentList, self).create(vals)
        return res

    def write(self, vals):
        if 'payment_ids' in vals:
            for element in vals.get('payment_ids'):
                if element[0] == 0:
                    # element[2]['payment_type'] = self.payment_type
                    # element[2]['partner_type'] = self.partner_type
                    # element[2]['partner_id'] = self.partner_id.id
                    # element[2]['crm_id'] = self.crm_id.id
                    # element[2]['payment_list_state'] = self.state
                    # element[2]['communication'] = self.communication
                    element[2]['payment_method_id'] = self.payment_method.id
        res = super(PaymentList, self).write(vals)
        for pay in self.payment_ids:
            pay.payment_type = pay.payment_list_id.payment_type

            pay.partner_type = pay.payment_list_id.partner_type
            pay.partner_id = pay.payment_list_id.partner_id

            pay.payment_list_state = pay.payment_list_id.state

            pay.crm_id = pay.payment_list_id.crm_id
            pay.communication = pay.payment_list_id.communication
        return res

    @api.model
    def default_get(self, fields):
        res = super(PaymentList, self).default_get(fields)
        return res

    @api.depends('payment_ids')
    def _get_amount_subtotal(self):
        for rec in self:
            if rec.payment_ids:
                rec.amount_subtotal = sum([pay.amount_vnd for pay in rec.payment_ids])
            else:
                rec.amount_subtotal = 0.0

    def cancel_line(self):
        print('Phiếu xác nhận')

    @api.onchange('payment_type')
    def _change_payment_type(self):
        for rec in self:
            if rec.payment_type and rec.payment_ids:
                for pay in rec.payment_ids:
                    payment = self.env['account.payment'].browse(pay._origin.id)
                    payment.write({
                        'payment_type': rec.payment_type
                    })

    @api.onchange('payment_date')
    def _change_payment_date(self):
        for rec in self:
            if rec.payment_date and rec.payment_ids:
                for pay in rec.payment_ids:
                    payment = self.env['account.payment'].browse(pay._origin.id)
                    payment.write({
                        'payment_date': rec.payment_date
                    })

    @api.onchange('communication')
    def _change_communication(self):
        for rec in self:
            if rec.communication and rec.payment_ids:
                for pay in rec.payment_ids:
                    payment = self.env['account.payment'].browse(pay._origin.id)
                    payment.write({
                        'communication': rec.communication
                    })

    @api.onchange('crm_id')
    def _change_crm_id(self):
        for rec in self:
            if rec.crm_id and rec.payment_ids:
                for pay in rec.payment_ids:
                    payment = self.env['account.payment'].browse(pay._origin.id)
                    payment.write({
                        'crm_id': rec.crm_id
                    })

    @api.onchange('partner_type')
    def _change_partner_type(self):
        for rec in self:
            if rec.partner_type and rec.payment_ids:
                for pay in rec.payment_ids:
                    payment = self.env['account.payment'].browse(pay._origin.id)
                    payment.write({
                        'partner_type': rec.partner_type
                    })

    @api.onchange('partner_id')
    def _change_partner_id(self):
        for rec in self:
            if rec.partner_id and rec.payment_ids:
                for pay in rec.payment_ids:
                    payment = self.env['account.payment'].browse(pay._origin.id)
                    payment.write({
                        'partner_id': rec.partner_id
                    })

    @api.onchange('company_id')
    def _change_company_id(self):
        for rec in self:
            if rec.company_id and rec.payment_ids:
                for pay in rec.payment_ids:
                    payment = self.env['account.payment'].browse(pay._origin.id)
                    payment.write({
                        'company_id': rec.company_id
                    })

    def number_to_words(self, total):
        return self.num2words_vnm(total)