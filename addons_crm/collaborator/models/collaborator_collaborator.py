import logging

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

GENDER = [('male', 'Nam'),
          ('female', 'Nữ'),
          ('transguy', 'Transguy'),
          ('transgirl', 'Transgirl'),
          ('other', 'Khác')]


class Collaborator(models.Model):
    _name = 'collaborator.collaborator'
    _description = 'Cộng tác viên'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'qrcode.mixin']

    code = fields.Char(string='Mã', index=True, default='New')
    name = fields.Char(string='Họ tên', index=True, tracking=True)

    passport = fields.Char('CMTND/CCCD ', tracking=True)
    passport_date = fields.Date('Ngày cấp')
    passport_issue_by = fields.Char('Nơi cấp')

    email = fields.Char('Email')
    phone = fields.Char('Điện thoại 1', tracking=True)
    mobile = fields.Char('Điện thoại 2')

    # category_source_id = fields.Many2one('crm.category.source', string='Nhóm nguồn')
    referrer_id = fields.Many2one('res.partner', string='Người giới thiệu',
                                  help='Nhân viên, khách hàng hoặc tổ chức giới thiệu cộng tác viên cho thương hiệu',
                                  tracking=True)

    source_id = fields.Many2one('utm.source', string='Nguồn cho Lead/Booking',
                                domain="[('is_collaborator', '=', True)]",
                                help='Nguồn của lead/booking khi lead/booking phát sinh từ cộng tác viên',
                                tracking=True)

    document_first = fields.Binary(string="Mặt trước")
    document_second = fields.Binary(string="Mặt sau")

    state = fields.Selection([('new', 'Mới'), ('effect', 'Hiệu lực'), ('expired', 'Hết hiệu lực')], string='Trạng thái',
                             default='new')

    qr_id = fields.Binary(string="QR ID", compute='_generate_qr_code')

    partner_id = fields.Many2one('res.partner', string='Khách hàng',
                                 help='Thông tin khách hàng của cộng tác viên, xem chân dung khách hàng, lịch sử làm dịch vụ')
    code_customer = fields.Char(string='Mã khách hàng', related='partner_id.code_customer')

    country_id = fields.Many2one('res.country', string="Quốc gia", default=241)
    note = fields.Text(string='Ghi chú', help='Thông tin ghi chú thêm cho cộng tác viên')

    booking_ids = fields.One2many('crm.lead', 'collaborator_id', string='Booking',
                                  domain=[('type', '=', 'opportunity')], auto_join=True)
    lead_ids = fields.One2many('crm.lead', 'collaborator_id', string='Lead',
                               domain=[('type', '=', 'lead')], auto_join=True)

    payment_ids = fields.One2many('collaborator.payment', 'collaborator_id', string='Phiếu Chi')
    account_ids = fields.One2many('collaborator.account', 'collaborator_id', string='Số tiền')
    transaction_ids = fields.One2many('collaborator.transaction', 'collaborator_id', string='Chi tiết hoa hồng')

    address = fields.Char('Nơi ở hiện tại', tracking=True)
    state_id = fields.Many2one(comodel_name='res.country.state', string='Tỉnh/thành phố',
                               domain="[('country_id', '=', country_id)]")
    district_id = fields.Many2one('res.country.district', string='Quận/huyện', domain="[('state_id', '=', state_id)]")
    ward_id = fields.Many2one('res.country.ward', string='Phường/xã', tracking=True)
    gender = fields.Selection(GENDER, string='Giới tính')
    date_of_birth = fields.Date('Ngày sinh')

    facebook_acc = fields.Char('Facebook')
    zalo_id = fields.Char('Zalo')
    viber = fields.Char('Viber')

    active = fields.Boolean('Active', default=True)

    # CTV nghỉ cần lưu lại lý do
    cancel_reason = fields.Char('Lý do hủy')

    # Các hợp đồng của CTV
    contract_ids = fields.One2many('collaborator.contract', 'collaborator_id')
    contract_count = fields.Integer(compute='_compute_contract_count', help='Số hợp đồng')
    # Các tài khoản ngân hàng
    bank_ids = fields.One2many('collaborator.bank', 'collaborator_id')
    permanent_address = fields.Char('Hộ khẩu thường trú')

    brand_id = fields.Many2one('res.brand', string='Thương hiệu', domain="[('is_collaborator', '=', True)]")
    # check_contract = fields.Selection([('1', 'Có'), ('2', 'Không')], default='2', string='Đã có hợp đồng hiệu lực')
    check_contract = fields.Selection([('1', 'Có'), ('2', 'Không')], default='2', string='Đã có hợp đồng hiệu lực', compute='compute_check_hd')
    company_id = fields.Many2one('res.company', string="Công ty")
    is_partner = fields.Boolean('Tạo từ partner')

    @api.onchange('phone')
    def get_information_partner(self):
        if self.phone:
            partner = self.env['res.partner'].sudo().search([('phone', '=', self.phone)])
            if partner:
                self.partner_id = partner.id
                self.name = partner.name
                self.gender = partner.gender
                self.country_id = partner.country_id.id
                self.state_id = partner.state_id.id
                self.district_id = partner.district_id.id
                self.ward_id = partner.ward_id.id
                self.address = partner.street
                self.date_of_birth = partner.birth_date
                self.passport = partner.pass_port
            else:
                self.partner_id = False
                self.name = ''
                self.gender = False
                self.country_id = False
                self.state_id = False
                self.address = False
                self.date_of_birth = False
                self.passport = False
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(Collaborator, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone', 'mobile']:
                fields[field_name]['exportable'] = False

        return fields

    def _compute_contract_count(self):
        for record in self:
            record.contract_count = self.env['collaborator.contract'].search_count(
                [('collaborator_id', '=', record.id)])
            # check_contract = self.env['collaborator.contract'].search_count(
            #     [('collaborator_id', '=', record.id), ('state', '=', 'effect')])
            # if check_contract == 1:
            #     record.check_contract = '1'

    def compute_check_hd(self):
        for rec in self:
            check_contract = self.env['collaborator.contract'].search([('collaborator_id', '=', rec.id), ('state', '=', 'effect')])
            if check_contract:
                rec.check_contract = '1'
            else:
                rec.check_contract = '2'
    # @api.depends('booking_id')
    # def get_only_booking(self):
    #     for record in self:
    #         record.only_booking = [(5,)]
    #         if record.booking_id:
    #             only_booking = record.booking_id.filtered(lambda b: b.type == 'opportunity')
    #             record.only_booking = [(6, 0, only_booking.ids)]

    # # def _get_company_currency(self):
    # #     for partner in self:
    # #         partner.currency_id = partner.sudo().company_id.currency_id

    # check Cộng tac viên theo thương hiệu
    # _sql_constraints = [
    #     ('passport_brand_uniq', 'unique (passport,brand_id)', 'Số CMTND/CCCD đã là công tác viên của thương hiệu'),
    #     ('phone_brand_uniq', 'unique (phone,brand_id)',
    #     'Số điện thoại đã là công tác viên của thương hiệu. Vui lòng sử dụng số khác'),
    # ]
    _sql_constraints = [
        ('default_phone_brand_unique', 'unique (phone,brand_id)',
         'CTV đã có thông tin trên hệ thống, vui lòng tìm kiếm CTV trong danh sách CTV để tạo hợp đồng.'),
        ('default_passport_brand_unique', 'unique (passport,brand_id)',
         'CTV đã có thông tin trên hệ thống, vui lòng tìm kiếm CTV trong danh sách CTV để tạo hợp đồng.')
    ]

    def _generate_qr_code(self):
        for item in self:
            base_url = '%s/web#id=%d&action=1291&view_type=form&model=%s' % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                item.id,
                item._name)
            item.qr_id = self.qrcode(base_url)

    # @api.depends('contract_ids.stage')
    def compute_check_state(self):
        for record in self:
            record.state = 'new'

    def action_partner(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Khách hàng'),
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.partner_id.id,
            'target': 'current',
            # 'flags': {'form': {'action_buttons': True}}
            # 'domain': [('email_from', 'in', self.mapped('email_from'))],
        }

    def action_contract(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hợp đồng'),
            'res_model': 'collaborator.contract',
            'view_mode': 'tree,form',
            'domain': [('collaborator_id', '=', self.id)],
        }

    # Tạo hợp đồng
    def open_form_create_contract(self):
        contract = self.contract_ids.search([('state', 'in', ['effect']),
                                             ('company_id', '=', self.env.company.ids),
                                             ('collaborator_id', '=', self.id)])
        if contract:
            raise ValidationError(
                'Bạn không thể tạo hợp đồng vì vẫn đang có hợp đồng %s đang còn hiệu lực' % contract.default_code)
        else:
            return {
                'name': 'Thông tin hợp đồng',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('collaborator.create_contract_wizard_view_form').id,
                'res_model': 'create.contract.wizard',
                'context': {
                    'default_name': self.id,
                    'default_source_id': self.source_id.id,
                    'default_passport': self.passport,
                    'default_email': self.email,
                    'default_phone': self.phone,
                    'default_mobile': self.mobile,
                    'default_bank_id': self.bank_ids[0].id if self.bank_ids else False,
                    'default_brand_id': self.brand_id.id,
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
            'view_id': self.env.ref('collaborator.view_form_collaborator_payment').id,
            'res_model': 'collaborator.payment',
            'context': {
                'default_collaborator_id': self.id,
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
                    'passport': self.passport,
                    'email': self.email,
                    'phone': self.phone,
                    'mobile': self.mobile,
                })

    # chuyển name
    def name_get(self):
        record = []
        for rec in self:
            if rec.code:
                record.append((rec.id, rec.name + " " + '[' + rec.code + ']'))
        return record

    # @api.onchange('collaborator')
    # def set_name_lead(self):
    # if self.type == 'lead':
    #     self.name = self.collaborator
    # if self.collaborator:
    #     self.name = self.collaborator.upper()
    # else:
    #     self.name = False

    # update dữ liệu nhân viên cho ctv
    # def update_source_ctv(self):
    # #     employee_ids = self.env['hr.employee'].search([('active', '=', True), ('employee_code', '!=', False)])
    # #     for employee in employee_ids:
    # #         check = self.env['utm.source.ctv'].search([('code', '=', employee.employee_code)])
    # #         if not check:
    # #             employee.env['utm.source.ctv'].sudo().create({
    # #                 'email': employee.work_email if employee.work_email else False,
    # #                 'code': employee.employee_code,
    # #                 'collaborator': employee.name,
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
            recs = self.search([('name', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search(['|', ('phone', operator, name), ('code', operator, name)] + args,
                               limit=limit)
        return recs.name_get()

    @api.onchange('category_source_id')
    def onchange_source_id(self):
        if self.category_source_id != self.source_id:
            self.source_id = False

    @api.constrains('phone', 'country_id')
    def check_phone(self):
        for rec in self:
            if rec.phone:
                if rec.phone.isdigit() is False:
                    raise ValidationError('Số điện thoại 1 khách hàng chỉ nhận giá trị số.')
                if ((10 > len(rec.phone)) or (len(rec.phone) > 10)) and rec.country_id == self.env.ref('base.vn'):
                        raise ValidationError('Số điện thoại tại Việt Nam chỉ chấp nhận 10 kí tự')
    @api.onchange('phone')
    def onchange_phone(self):
        for rec in self:
            if rec.phone:
                if rec.phone.isdigit() is False:
                    raise ValidationError('Số điện thoại 1 khách hàng chỉ nhận giá trị số.')

    # @api.constrains('passport')
    # def check_passport(self):
    #     for rec in self:
    #         if rec.passport:
    #             if rec.passport.isdigit() is False:
    #                 raise ValidationError('CMTND/CCCD khách hàng chỉ nhận giá trị số.')
                # if rec.passport:
                # if company_id.code == self.company_id.code:
                #     raise ValidationError('CMTND/CCCD phải là duy nhất!')

    @api.constrains('mobile')
    def check_mobile(self):
        for rec in self:
            if rec.mobile:
                if rec.mobile.isdigit() is False:
                    raise ValidationError('Số điện thoại 2 khách hàng chỉ nhận giá trị số.')
                if ((10 > len(self.phone)) or (len(self.phone) > 10)) and self.country_id == self.env.ref('base.vn'):
                    raise ValidationError('Số điện thoại ở Việt Nam chỉ chấp nhận 10 kí tự')

    @api.model
    def create(self, vals):
        if not vals['is_partner']:
            if vals['brand_id'] and vals['phone'] and vals['passport']:
                collaborator = self.env['collaborator.collaborator'].sudo().search(
                    ['|', ('phone', '=', vals['phone']), ('passport', '=', vals['passport']),
                     ('brand_id', '=', vals['brand_id'])])
                if collaborator.company_id:
                    raise ValidationError('Không thể tạo CTV do trùng thông tin SĐT/CCCD với CTV %s đã ký hợp đồng tại chi nhánh %s.' %(collaborator.name,collaborator.company_id.name))
        else:
            if vals['brand_id'] and vals['partner_id'] and vals['passport']:
                partner_id = self.env['res.partner'].sudo().browse(vals['partner_id'])
                collaborator = self.env['collaborator.collaborator'].sudo().search(
                    ['|', ('phone', '=', partner_id.phone), ('passport', '=', vals['passport']),
                     ('brand_id', '=', vals['brand_id'])])
                if collaborator.company_id:
                    raise ValidationError('Không thể tạo CTV do trùng thông tin SĐT/CCCD với CTV %s đã ký hợp đồng tại chi nhánh %s.' %(collaborator.name,collaborator.company_id.name))
        if vals.get('code', 'New') == 'New':
            # Fixme mỗi chi nhánh cần 1 sequence riêng @ToanNH xử lý
            source_id = self.env['utm.source'].browse(vals['source_id'])
            short_code_brand = self.env['res.brand'].browse(vals['brand_id'])
            if vals['brand_id'] == 1:
                if 'source_id' in vals and vals['source_id']:
                    if source_id.tag:
                        vals['code'] = short_code_brand.short_code + source_id.tag + '-' + self.env[
                            'ir.sequence'].next_by_code('collaborator.collaborator.sequence.kn')
                    else:
                        raise ValidationError('Bạn hãy cấu hình mã nguồn trước khi tạo thông tin cộng tác viên.')
            elif vals['brand_id'] == 3:
                if 'source_id' in vals and vals['source_id']:
                    if source_id.tag:
                        vals['code'] = short_code_brand.short_code + source_id.tag + '-' + self.env[
                            'ir.sequence'].next_by_code('collaborator.collaborator.sequence.pa')
                    else:
                        raise ValidationError('Bạn hãy cấu hình mã nguồn trước khi tạo thông tin cộng tác viên.')
        if vals.get('name'):
            vals['name'] = vals['name'].title()
        res = super(Collaborator, self).create(vals)
        return res

    def write(self, values):
        if 'active' in values and not values['active']:
            if self.state == 'effect':
                raise UserError(_('Bạn không thể lưu trữ khi cộng tác viên còn hiệu lực.'))
            pass
        result = super(Collaborator, self).write(values)
        return result

    def unlink(self):
        for rec in self:
            if rec.state in ("effect", "expired"):
                raise UserError(_('Bạn chỉ có thể xoá khi ở trạng thái nháp.'))
        return super(Collaborator, self).unlink()

    def create_lead(self):
        self.ensure_one()
        # contract = self.contract_ids.search([('state', '=', 'effect')], limit=1)
        contract = self.env['collaborator.contract'].sudo().search([('collaborator_id', '=', self.id), ('state', '=', 'effect')])
        if 'không xác định' in contract[0].company_id.name.lower():
            return {
                'name': 'Tạo Lead CTV',
                'view_mode': 'form',
                'res_model': 'collaborator.collaborator.create.lead',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('collaborator.collaborator_collaborator_create_lead').id,
                'context': {
                    'default_collaborator_id': self.id,
                    'default_company_id': contract[0].company_id.id if contract else False,
                    'default_check_company_kxd_pa': True
                },
                'target': 'new'
            }
        else:
            return {
                'name': 'Tạo Lead CTV',
                'view_mode': 'form',
                'res_model': 'collaborator.collaborator.create.lead',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('collaborator.collaborator_collaborator_create_lead').id,
                'context': {
                    'default_collaborator_id': self.id,
                    'default_company_id': contract[0].company_id.id if contract else False
                },
                'target': 'new'
            }

    @api.model
    def action_domain_collaborator(self):
        # action = self.env.ref('collaborator.collaborator_collaborator_action').read()[0]
        # action['domain'] = [
        #     '|', '|', '&',
        #     ('brand_id', 'in', self.env.user.company_ids.brand_id.ids),
        #     ('company_id', 'in', self.env.user.company_ids.ids),
        #     ('create_uid', '=', self.env.user.id),
        #     ('company_id', '=', False)
        # ]
        # return action
        domain = [
            '|',
            '&',
            ('brand_id', 'in', self.env.user.company_ids.brand_id.ids),
            ('company_id', 'in', self.env.user.company_ids.ids),
            '&',
            ('brand_id', 'in', self.env.user.company_ids.brand_id.ids),
            '|',
            ('company_id', '=', False),
            ('create_uid', '=', self.env.user.id),
        ]
        action = {
            'name': 'Cộng tác viên',
            'res_model': 'collaborator.collaborator',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_id': False,
            'view_type': 'form',
            'domain': domain,
            'context': {'ir.ui.view_scroller': True},  # Thêm context này để không sử dụng cache
            'target': 'current',
            'auto_search': False,
        }
        return action