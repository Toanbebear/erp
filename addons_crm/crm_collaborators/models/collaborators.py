import logging

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class CRMCollaborators(models.Model):
    _name = 'crm.collaborators'
    _description = 'Cộng tác viên'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'qrcode.mixin']

    name = fields.Char(index=True)
    check_ctv = fields.Boolean('Check cộng tác viên', store=True)
    code_collaborators = fields.Char('Mã cộng tác viên:', index=True, default='New')
    collaborators = fields.Char(string='Tên cộng tác viên', tracking=True)  # translate=True
    pass_port = fields.Char('CMTND/CCCD ', tracking=True)
    email = fields.Char('Email')
    phone = fields.Char('Điện thoại 1', tracking=True)
    mobile = fields.Char('Điện thoại 2')
    category_source_id = fields.Many2one('crm.category.source', string='Nhóm nguồn')
    source_id = fields.Many2one('utm.source', string='Nguồn', domain="[('category_id', '=', category_source_id)]",
                                tracking=True)
    documents = fields.Binary(string="File CMTND/CCCD")
    document_name = fields.Char(string="File name ")
    state = fields.Selection(
        [('unprocessed', 'Chưa xử lý'), ('new', 'Hiệu lực'), ('done', 'Hết hiệu lực'), ('open', 'Mở lại'),
         ('cancel', 'Hủy')],
        string='Trạng thái', store=True, default='unprocessed', tracking=True, compute='compute_check_state')
    contract_ids = fields.One2many('collaborators.contract', 'collaborators_id')
    bank = fields.Char(string='Ngân hàng')
    user_bank = fields.Char('Tên chủ tài khoản')
    card_number = fields.Char(string='Số tài khoản ngân hàng')
    qr_id = fields.Binary(string="QR ID", compute='_generate_qr_code')
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    code_customer = fields.Char(string='Mã khách hàng', related='partner_id.code_customer', store=True)
    country_id = fields.Many2one('res.country', string="Quốc gia", default=241)
    active = fields.Boolean('Active', default=True)
    note = fields.Text(string='Ghi chú')
    booking_id = fields.One2many('crm.lead', 'collaborators_id', string='booking',
                                 domain="[('type','=','opportunity')]", )
    account_payment_ctv = fields.One2many('account.payment.ctv', 'collaborators_id', string='Phiếu Chi')
    payment_ctv = fields.One2many('crm.payment.ctv', 'collaborators_id', 'Số tiền')
    detail_sale_ids = fields.One2many('crm.detail.sale', 'collaborators_id', 'Chi tiết hoa hồng')
    address = fields.Char('Địa chỉ')
    sex = fields.Selection([
        ('male', 'Nam'), ('female', 'Nữ')], 'Giới tính')
    year_of_birth = fields.Date('Ngày sinh')
    pass_port_date = fields.Date('Ngày cấp')
    pass_port_issue_by = fields.Char('Nơi cấp')
    facebook_acc = fields.Char('Tài khoản Facebook/Zalo')
    only_booking = fields.Many2many('crm.lead', compute='get_only_booking')
    cancel_note = fields.Char('Lý do hủy')

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(CRMCollaborators, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone', 'mobile']:
                fields[field_name]['exportable'] = False

        return fields

    @api.depends('booking_id')
    def get_only_booking(self):
        for record in self:
            record.only_booking = [(5,)]
            if record.booking_id:
                only_booking = record.booking_id.filtered(lambda b: b.type == 'opportunity')
                record.only_booking = [(6, 0, only_booking.ids)]

    # # def _get_company_currency(self):
    # #     for partner in self:
    # #         partner.currency_id = partner.sudo().company_id.currency_id

    # check CCCD
    _sql_constraints = [
        ('pass_port_unique', 'unique(pass_port)', 'CMTND/CCCD phải là duy nhất !'),
        ('phone_unique', 'unique(phone)', 'Số điện thoại phải là duy nhất! Đã có cộng tác viên đăng ký với số này.'),
    ]

    def _generate_qr_code(self):
        for item in self:
            base_url = '%s/web#id=%d&action=1291&view_type=form&model=%s' % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                item.id,
                item._name)
            item.qr_id = self.qrcode(base_url)

    @api.depends('contract_ids.stage')
    def compute_check_state(self):
        for record in self:
            if not record.contract_ids:
                record.state = 'unprocessed'
            else:
                stages = record.contract_ids.mapped('stage')
                if 'new' in stages:  # done
                    record.state = 'new'
                elif all(stage == 'draft' for stage in stages):  # done
                    record.state = 'new'
                elif all(stage == 'done' for stage in stages):  # done
                    record.state = 'done'
                elif all(stage == 'cancel' for stage in stages):  # done
                    record.state = 'done'
                elif all(stage in ['draft', 'done', 'cancel'] for stage in stages):  # done
                    record.state = 'new'
                elif all(stage in ['draft', 'cancel'] for stage in stages):  # done
                    record.state = 'new'
                elif all(stage in ['done', 'cancel'] for stage in stages):  # done
                    record.state = 'done'
                elif all(stage in ['draft', 'done'] for stage in stages):  # done
                    record.state = 'new'
                else:
                    record.state = 'unprocessed'

    def create_contract(self):  # Tạo hợp đồng
        # hopdong = self.contract_ids.search([('stage', 'in', ['new', 'open']), ('company_id', '=', self.env.company.ids)])
        # if hopdong:
        #     raise ValidationError('Bạn không thể tạo hợp đồng vì vẫn đang có hợp đồng được sử dụng')
        # else:
        return {
            'name': 'THÔNG TIN HỢP ĐỒNG',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_collaborators.check_partner_view_form').id,
            'res_model': 'check.partner',
            'context': {
                'default_name': self.id,
                'default_source_id': self.source_id.id,
                'default_pass_port': self.pass_port,
                'default_email': self.email,
                'default_phone': self.phone,
                'default_mobile': self.mobile,
            },
            'target': 'new',
        }

    # Tạo phiếu chi cộng tác viên
    def create_payment(self):
        return {
            'name': 'THÔNG TIN HỢP ĐỒNG',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_collaborators.view_form_account_payment_ctv').id,
            'res_model': 'account.payment.ctv',
            'context': {
                'default_collaborators_id': self.id,
            },
            'target': 'current',
        }

    def reopen_ctv(self):  # Mở lại
        self.state = 'open'

    def create_draft(self):
        self.state = 'unprocessed'

    def update_info(self):  # cập nhật thông tin
        self.state = 'new'
        if self.contract_ids:
            for rec in self.contract_ids:
                rec.write({
                    # 'documents': self.documents,
                    'pass_port': self.pass_port,
                    'email': self.email,
                    'phone': self.phone,
                    'mobile': self.mobile,
                })

    # chuyển name
    def name_get(self):
        record = []
        for rec in self:
            if rec.pass_port:
                record.append((rec.id, rec.collaborators + " " + '[' + rec.code_collaborators + ']'))
            else:
                record.append((rec.id, rec.collaborators + " "))
        return record

    @api.onchange('collaborators')
    def set_name_lead(self):
        # if self.type == 'lead':
        #     self.name = self.collaborators
        if self.collaborators:
            self.name = self.collaborators.upper()
        else:
            self.name = False

    # update dữ liệu nhân viên cho ctv
    # def update_source_ctv(self):
    # #     employee_ids = self.env['hr.employee'].search([('active', '=', True), ('employee_code', '!=', False)])
    # #     for employee in employee_ids:
    # #         check = self.env['utm.source.ctv'].search([('code', '=', employee.employee_code)])
    # #         if not check:
    # #             employee.env['utm.source.ctv'].sudo().create({
    # #                 'email': employee.work_email if employee.work_email else False,
    # #                 'code': employee.employee_code,
    # #                 'collaborators': employee.name,
    # #                 'phone': employee.mobile_phone,
    # #                 'brand_id' : employee.root.department,
    # #                 'category_source_id': 66, #id của nguồn
    # #                 'source_id': 77, #id nhóm nguồn
    # #             })

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('collaborators', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search(['|', ('phone', operator, name), ('code_collaborators', operator, name)] + args,
                               limit=limit)
        return recs.name_get()

    @api.onchange('category_source_id')
    def onchange_source_id(self):
        if self.category_source_id != self.source_id:
            self.source_id = False

    @api.constrains('phone', 'country_id')
    def check_phone(self):
        for rec in self:
            if rec.phone and rec.country_id:
                if rec.phone.isdigit() is False:
                    raise ValidationError('Số điện thoại 1 khách hàng chỉ nhận giá trị số')
                # if (10 > len(rec.phone)) or (len(rec.phone) > 10):
                #     if rec.country_id == self.env.ref('base.vn'):
                #         raise ValidationError('Số điện thoại 1 chỉ chấp nhận 10 kí tự')

    @api.constrains('pass_port')
    def check_pass_port(self):
        for rec in self:
            if rec.pass_port:
                if rec.pass_port.isdigit() is False:
                    raise ValidationError('CMTND/CCCD khách hàng chỉ nhận giá trị số')
                # if rec.pass_port:
                # if company_id.code == self.company_id.code:
                #     raise ValidationError('CMTND/CCCD phải là duy nhất!')

    @api.constrains('mobile')
    def check_mobile(self):
        for rec in self:
            if rec.mobile:
                if rec.mobile.isdigit() is False:
                    raise ValidationError('Số điện thoại 2 khách hàng chỉ nhận giá trị số')
                # if (10 > len(self.phone)) or (len(self.phone) > 10) and (self.country_id == self.env.ref('base.vn')):
                #     raise ValidationError('Số điện thoại ở Việt Nam chỉ chấp nhận 10 kí tự')

    @api.onchange('phone')
    def check_partner_name(self):
        if self.phone:
            if self.phone.isdigit() is False:
                raise ValidationError('Số điện thoại 1 khách hàng chỉ nhận giá trị số')
            if not self.env.context.get('default_phone'):
                partner = self.env['res.partner'].search([('phone', '=', self.phone)])

                ctv_ids = self.env['crm.collaborators'].search([('phone', '=', self.phone)], order="id asc", limit=1)
                if partner:
                    self.partner_id = partner.id
                    self.collaborators = partner.name
                    self.country_id = partner.country_id.id
                    self.mobile = partner.mobile
                    self.pass_port = partner.pass_port
                    self.bank = ctv_ids.bank
                    self.card_number = ctv_ids.card_number
                    self.email = ctv_ids.email
                else:
                    self.partner_id = False
                    self.collaborators = ctv_ids.name
                    self.country_id = ctv_ids.country_id.id if ctv_ids else self.country_id
                    self.mobile = ctv_ids.mobile
                    self.pass_port = ctv_ids.pass_port
                    self.bank = ctv_ids.bank
                    self.card_number = ctv_ids.card_number
                    self.email = ctv_ids.email
            if (10 > len(self.phone)) or (len(self.phone) > 10) and (self.country_id == self.env.ref('base.vn')):
                raise ValidationError('Số điện thoại ở Việt Nam chỉ chấp nhận 10 kí tự')

    @api.model
    def create(self, vals):
        if vals.get('code_collaborators', 'New') == 'New':
            vals['code_collaborators'] = self.env['ir.sequence'].next_by_code('crm.collaborators.sequence') or 'New'

        if vals.get('collaborators'):
            vals['collaborators'] = vals['collaborators'].title()
        res = super(CRMCollaborators, self).create(vals)
        return res

    def write(self, vals):
        return super(CRMCollaborators, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != "unprocessed":
                raise UserError(_('Bạn chỉ có thể xoá khi ở trạng thái nháp'))

        return super(CRMCollaborators, self).unlink()


class CtvLead(models.Model):
    _inherit = 'crm.lead'

    collaborators_id = fields.Many2one('crm.collaborators', string="Tên cộng tác viên",
                                       domain="[('source_id', '=', source_id)]",
                                       help='Cộng tác viên Hồng Hà')
    check_ctv = fields.Boolean('check CTV')

    @api.onchange('source_id')
    def onchange_collaborators_id(self):
        if self.source_id != self.collaborators_id and 'default_collaborators_id' not in self._context:
            self.collaborators_id = False

    # compute
    @api.onchange('category_source_id')
    def onchange_category_source_id(self):
        if self.category_source_id.id == 66:
            self.check_ctv = True
        else:
            self.check_ctv = False


class AccountPaymentCollaborators(models.Model):
    _inherit = 'account.payment'

    collaborators_id = fields.Many2one('crm.collaborators', string="Cộng tác viên")
    contract_id = fields.Many2one('collaborators.contract', string='Hợp đồng')
    payment_type = fields.Selection(selection_add=[('outpay', 'Chi tiền cộng tác viên')])

    collaborators_amount = fields.Monetary('Tổng tiền hiện có', help='Tổng tiền của cộng tác viên ')
    check_ctv = fields.Boolean('Check cộng tác viên', default=False)
    payment_ctv = fields.Many2one('account.payment.ctv', 'Phiếu chi ctv')


class CRMSaleOrderCTV(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(CRMSaleOrderCTV, self).action_confirm()
        hop_dong = self.booking_id.collaborators_id.contract_ids
        if self.booking_id.collaborators_id:
            tong = 0
            for so in self:
                sols = [(s.product_id.default_code, s) for s in so.order_line]
                for hd in hop_dong.filtered(
                        lambda hd: hd.company_id == self.company_id and hd.stage in ('new', 'open')):
                    for line in hd.crm_line_ids:
                        for ser in line.service_id:
                            for sol in sols:
                                if sol[0] in ser.default_code:
                                    sum_amount = sol[1].price_subtotal * line.discount_percent / 100
                                    tong += sum_amount
                                    kham = [(wk.name, wk) for wk in
                                            so.booking_id.walkin_ids.filtered(lambda wl: wl.sale_order_id.id == so.id)],

                                    if sum_amount > 0 :
                                        # Chi tiết
                                        detail = so.env['crm.detail.sale'].sudo().create({
                                            'collaborators_id': so.booking_id.collaborators_id.id,
                                            'contract_id': hd.id,
                                            'company_id': so.booking_id.company_id.id,
                                            'brand_id': so.brand_id.id,
                                            'booking_id': so.booking_id.id,
                                            'sale_order': so.id,
                                            'service_id': ser.id,
                                            'walkin_id': kham[0][0][1].id,
                                            'service_date': so.date_order,
                                            'amount_total': sol[1].price_subtotal,
                                            'amount_used': sum_amount,
                                            'discount_percent': line.discount_percent,
                                        })
                        if tong > 0:
                            tien_ctv = self.env['crm.payment.ctv'].sudo().search(
                                [('collaborators_id', '=', self.booking_id.collaborators_id.ids),
                                 ('company_id', '=', self.booking_id.company_id.ids)])
                            #  Tiền
                            if tien_ctv:
                                tien_ctv.write({
                                    'collaborators_id': so.booking_id.collaborators_id.id,
                                    'contract_id': hd.id,
                                    'company_id': so.booking_id.company_id.id,
                                    'amount_total': tong + tien_ctv.amount_total,
                                })
                            else:
                                so.env['crm.payment.ctv'].sudo().create({
                                    'collaborators_id': so.booking_id.collaborators_id.id,
                                    'contract_id': hd.id,
                                    'company_id': so.booking_id.company_id.id,
                                    'amount_total': tong,
                                })

        return res
