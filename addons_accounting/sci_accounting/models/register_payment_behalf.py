from odoo import fields, models, api, _
import json
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
from lxml import etree

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}


class RegisterPaymentBehalf(models.Model):
    _name = 'account.register.payment.behalf'
    _description = 'Quản lý đề nghị chi hộ'
    _order = 'date_register, label desc'

    name = fields.Char(string='Tên phiếu')
    date_register = fields.Date(string='Ngày tạo', required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', domain="[('type', 'in', ('general', )), ('company_id', '=', company_id)]", string='Sổ nhật ký')
    company_id = fields.Many2one('res.company', string='Chi nhánh', default=lambda self: self.env.company)
    communication = fields.Char(string='Diễn giải', store=True)

    behalf_lines = fields.One2many(comodel_name='account.register.payment.behalf.line', inverse_name='register_payment')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, required=True, string='Currency', default=lambda rec: rec.env.company.currency_id)
    amount_total = fields.Monetary(string='Tổng tiền đề nghị', compute='_get_amount_total')
    amount_total_approval = fields.Monetary(string='Tổng tiền duyệt chi', compute='_get_amount_total_approval')

    user_id = fields.Many2one(comodel_name='res.users', string='Người lập', default=lambda self: self.env.user)
    payment_method_id = fields.Many2one('account.payment.method', string='Phương thức', default=[('payment_type', '=', 'outbound')])

    is_debt = fields.Boolean(string='Có/Không đề nghị thanh toán công nợ', store=True, default=False)
    state = fields.Selection(selection=[('draft', 'Draft'), ('wait', 'Chờ xử lý'), ('sent', 'Sent'), ('wait_payment', 'Chờ thanh toán'), ('posted', 'Posted'), ('cancel', 'Cancelled')],
                             string='Status', required=True, readonly=True, copy=False, tracking=True, default='draft')
    type = fields.Selection(selection=[('dn', 'Đề nghị'), ('dc', 'Duyệt chi')], string='Loại đề nghị', required=True)
    original_record = fields.Many2one(comodel_name='account.register.payment.behalf', string='Phiếu gốc.')
    label = fields.Selection(selection=[('1', 'Bình thường'), ('2', 'Ưu tiên'), ('3', 'Khẩn cấp')], string='Phân loại mức ưu tiên')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(RegisterPaymentBehalf, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])

        if view_type == 'form':
            for node in doc.xpath("//field"):
                node.set("attrs", "{'readonly':[('state','!=', 'draft')]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = "[('state','!=','draft')]"
                node.set('modifiers', json.dumps(modifiers))

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def action_draft(self):
        self.ensure_one()
        self.name = _('New')
        self.state = 'draft'

    def action_sent(self):
        # Tạo mới phiếu duyệt chị. gắn cho công ty mới.
        val = {
            'name': _('Gửi phiếu đề nghị chi hộ tới chi nhánh'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('sci_accounting.account_payment_behalf_register_from').id,
            'res_model': 'register.payment.behalf.wizard',
            'target': 'new',
            'context': {
                'default_register_payment': self.id,
            }
        }
        return val

    def action_confirm(self):
        if self._context.get('name', _('New')) == _('New'):
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.date_register))
            self.name = self.env['ir.sequence'].next_by_code('account.payment.behalf', sequence_date=seq_date) or _('New')
            self.write({'state': 'wait'})

    @api.onchange('company_id')
    def _get_communication(self):
        for rec in self:
            if rec.company_id:
                rec.communication = '%s đề nghị chi hộ' % (rec.company_id.name)

    @api.model
    def default_get(self, fields_list):
        rec = super(RegisterPaymentBehalf, self).default_get(fields_list)
        return rec

    @api.model
    def create(self, vals_list):
        return super(RegisterPaymentBehalf, self).create(vals_list)

    @api.depends('behalf_lines')
    def _get_amount_total(self):
        # Tính tổng số tiền đề nghị trong từng line
        for rec in self:
            total = sum(rec.behalf_lines.mapped('amount_register')) if rec.behalf_lines else 0.0
            rec.amount_total = total

    @api.depends('behalf_lines')
    def _get_amount_total_approval(self):
        # Tính tổng số tiền duyệt trong từng line
        for rec in self:
            total = sum(rec.behalf_lines.mapped('amount_approval')) if rec.behalf_lines else 0.0
            rec.amount_total_approval = total

    def _prepare_payment_vals(self, invoices):

        amount = self._get_amount_approval_by_partner(invoices[0].partner_id)

        values = {
            'payment_type': 'outbound',
            'journal_id': self.journal_id.id,
            'payment_method': 'tm',
            'payment_method_id': 2,
            'payment_date': self.date_register,
            'communication': " Và HĐ ".join(i.invoice_payment_ref or i.ref or i.name for i in invoices),
            'invoice_ids': [(6, 0, invoices.ids)],
            'amount': abs(amount),
            'currency_id': invoices[0].currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'partner_bank_account_id': invoices[0].invoice_partner_bank_id.id,
            'company_id': self.company_id.id,
            'company2_id': self.sudo().original_record.company_id.id,
            'is_payment_for_share': True,
            'payment_reference': self.name,
            'behalf_id': self.id,
        }
        return values

    def get_payments_vals(self):

        grouped = defaultdict(lambda: self.env["account.move"])

        # for inv in self.sudo().behalf_lines.invoice:
        #     grouped[(inv.commercial_partner_id, inv.currency_id, inv.invoice_partner_bank_id, MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type])] += inv
        for line in self.behalf_lines:
            if line.approval not in ('cd', 'refuse'):
                inv = line.sudo().invoice
                grouped[(inv.commercial_partner_id, inv.currency_id, inv.invoice_partner_bank_id, MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type])] += inv

        return [self._prepare_payment_vals(invoices) for invoices in grouped.values()]

    def _get_amount_approval_by_partner(self, partner):
        result = 0.0
        for rec in self.behalf_lines:
            if rec.partner_id == partner and rec.approval not in ('cd', 'refuse'):
                result += rec.amount_approval
        return result

    def create_payments(self):
        # Kiểm tra trạng thái xét duyệt của các hóa đơn trong bảng kê.
        check = False
        if self.behalf_lines:
            check = all([rec.approval != 'cd' for rec in self.behalf_lines])
        if check:
            payments = self.env['account.payment'].create(self.get_payments_vals())
            action_vals = {
                'name': _('Payments'),
                'domain': [('id', 'in', payments.ids)],
                'res_model': 'account.payment',
                'view_id': False,
                'views': [(self.env.ref('sci_accounting.account_payment_transfer_tree').id, 'tree'), (self.env.ref('sci_accounting.view_account_payment_behalf_transfer_form').id, 'form')],
                'type': 'ir.actions.act_window',
            }
            if len(payments) == 1:
                action_vals.update({'res_id': payments[0].id, 'view_mode': 'form'})
            else:
                action_vals['view_mode'] = 'tree,form'
            self.write({'state': 'wait_payment'})
            return action_vals

        else:
            raise UserError(_("Có hóa đơn chưa được xét duyệt"))

    # Duyệt qua đề nghị thanh toán chi phí behalf_lines_cost. Mỗi dòng đề nghị nếu có trạng thái là đã duyệt thì lấy số tiền cột số tiền duyệt chi để tạo ra account.payment
    def create_payment_cost(self):
        check = False
        if self.behalf_lines:
            check = all([rec.approval != 'cd' for rec in self.behalf_lines])

        result = [self._prepare_payment_cost_vals(line) for line in self.behalf_lines if line.approval not in ('cd', 'refuse')]
        if check:
            payments = self.env['account.payment'].create(result)
            action_vals = {
                'name': _('Payments'),
                'domain': [('id', 'in', payments.ids)],
                'res_model': 'account.payment',
                'view_id': False,
                'views': [(self.env.ref('sci_accounting.account_payment_transfer_tree').id, 'tree'), (self.env.ref('sci_accounting.view_account_payment_behalf_transfer_form').id, 'form')],
                'type': 'ir.actions.act_window',
            }
            if len(payments) == 1:
                action_vals.update({'res_id': payments[0].id, 'view_mode': 'form'})
            else:
                action_vals['view_mode'] = 'tree,form'
            self.write({'state': 'wait_payment'})
            return action_vals
        else:
            raise UserError(_("Có hóa đơn chưa được xét duyệt"))

    def _prepare_payment_cost_vals(self, line):
        behalf_parent = self.sudo().original_record
        values = {
            'payment_type': 'outbound',
            'journal_id': self.journal_id.id,
            'payment_method': 'tm',
            'payment_method_id': 2,
            'payment_date': self.date_register,
            'communication': 'Thanh toán hộ chi nhánh: ' + behalf_parent.company_id.name + ' ' + line.communication,
            'invoice_ids': [],
            'amount': abs(line.amount_approval),
            'currency_id': line.currency_id.id,
            'partner_id': self.env['res.partner'].sudo().search([('id', '=', behalf_parent.company_id.partner_id.id)]).id,
            'partner_type': 'supplier',
            'company_id': self.company_id.id,
            'company2_id': behalf_parent.company_id.id,
            'is_payment_for_share': True,
            'behalf_id': self.id,
        }
        return values


class RegisterPaymentBehalfLine(models.Model):
    _name = 'account.register.payment.behalf.line'
    _description = 'Register Payment Behalf Line'

    sequence = fields.Integer(string='Sequence', default=10)
    register_payment = fields.Many2one(comodel_name='account.register.payment.behalf')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Đối tác')
    invoice = fields.Many2one(comodel_name='account.move', string='Số hóa đơn',
                              domain="[('partner_id', '=', partner_id), ('invoice_payment_state', '!=', 'paid')]")
    invoice_date = fields.Date(string='Ngày hóa đơn', related='invoice.invoice_date')
    amount_total = fields.Monetary(string='Tổng tiền hóa đơn', related='invoice.amount_total', store=True)
    amount_paid = fields.Monetary(string='Tổng tiền đã thanh toán', store=True, compute='_get_amount_paid')
    amount_residual = fields.Monetary(string='Tổng tiền đến hạn thanh toán', related='invoice.amount_residual', store=True)
    amount_register = fields.Monetary(string='Số tiền đề nghị')
    # currency_id = fields.Many2one('res.currency', store=True, readonly=True, required=True, string='Currency',
    #                                 related='invoice.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, string='Currency', default=lambda self: self.env.company.currency_id)
    state_invoice = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, copy=False, tracking=True,
        default='draft', related='invoice.state')
    approval = fields.Selection(selection=[('cd', 'Chở duyệt'), ('all', 'Duyệt toàn phần'), ('half', 'Duyệt một phần'), ('refuse', 'Từ chối')], string='Tình trạng duyệt', default='cd')
    amount_approval = fields.Monetary(string='Số tiền duyệt chi')
    communication = fields.Char(string='Diễn giải chi tiết')
    state = fields.Selection(selection=[('draft', 'Draft'), ('sent', 'Sent'), ('wait', 'Chờ xử lý'), ('wait_payment', 'Chờ thanh toán'), ('posted', 'Posted'), ('cancel', 'Cancelled')],
                             string='Status Line',
                             related='register_payment.state', readonly=True, default='draft')

    @api.onchange('approval')
    def _get_amount_approval(self):
        for rec in self:
            if rec.amount_register != 0.0 and rec.approval == 'all':
                rec.amount_approval = rec.amount_register
            else:
                rec.amount_approval = 0.0

    @api.onchange('invoice')
    def _get_amount_paid(self):
        for rec in self:
            widget = rec.invoice.invoice_payments_widget
            if widget and widget != 'false':
                content = json.loads(rec.invoice.invoice_payments_widget)['content']
                amount = [element['amount'] for element in content]
                rec.amount_paid = sum(amount)
            else:
                rec.amount_paid = 0.0

    @api.model
    def create(self, vals):
        cur_id = self.env.user.company_id.currency_id.id
        vals['currency_id'] = cur_id
        return super(RegisterPaymentBehalfLine, self).create(vals)

    @api.onchange('invoice')
    def _get_default_amount_approval(self):
        for line in self:
            if line.invoice:
                line.amount_register = line.invoice.amount_residual

    @api.constrains('amount_register')
    def _check_amount_register(self):
        for line in self:
            if line.invoice:
                if line.amount_register < 0.0 or line.amount_register > line.invoice.amount_residual:
                    raise ValidationError(_("Số tiền đề nghị không hợp lệ."))

