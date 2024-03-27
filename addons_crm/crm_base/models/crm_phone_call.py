from odoo.osv import expression
from dateutil.relativedelta import relativedelta
from odoo import fields, api, models, _
from lxml import etree
import json
from datetime import datetime, date, timedelta
from odoo.exceptions import ValidationError


class PhoneCall(models.Model):
    _name = "crm.phone.call"
    _description = 'Phone Call'
    _inherit = "mail.thread"

    name = fields.Char(string="Name", tracking=True)
    subject = fields.Char(string='Chủ đề', tracking=True)
    user_id = fields.Many2one('res.users', string='Người xác nhận', tracking=True, default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Khách hàng', tracking=True)
    phone = fields.Char('Phone', tracking=True)
    direction = fields.Selection([('in', 'Gọi vào'), ('out', 'Gọi ra')], string='Hướng gọi', tracking=True)
    desc = fields.Text('Mô tả', tracking=True)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', tracking=True, related='company_id.brand_id',
                               store=True)
    company_id = fields.Many2one('res.company', string='Công ty', tracking=True,
                                 default=lambda self: self.env.company)
    company2_id = fields.Many2many('res.company', string='Công ty share', related="crm_id.company2_id")
    crm_id = fields.Many2one('crm.lead', string='Booking liên quan', tracking=True, domain='[("type","!=","lead")]')
    # crm_line_id = fields.One2many('crm.line', related='crm_id.crm_line_ids', store=True)
    order_id = fields.Many2one('sale.order', string='Order liên quan', tracking=True)
    country_id = fields.Many2one('res.country', string='Quốc gia', default=241, tracking=True)
    state_id = fields.Many2one('res.country.state', string='Thành phố', tracking=True)
    street = fields.Char('Street', tracking=True)
    type_crm_id = fields.Many2one('crm.type', string='Loại phone call', domain="[('phone_call','=',True)]",
                                  tracking=True)
    # stage_id = fields.Many2one('crm.stage', string='Trạng thái', tracking=True, domain="[('crm_type_id','in',type_crm_id)]")
    support_rating = fields.Selection(
        [('1', 'Rất tệ'), ('2', 'Không hài lòng'), ('3', 'Bình thường'), ('4', 'Hài lòng'), ('5', 'Rất hài lòng')],
        string='Đánh giá hài lòng')
    support_quality = fields.Selection(
        [('1', 'Rất tệ'), ('2', 'Không hài lòng'), ('3', 'Bình thường'), ('4', 'Hài lòng'), ('5', 'Rất hài lòng')],
        string='Đánh giá chất lượng phục vụ')
    service_quality = fields.Selection(
        [('1', 'Rất tệ'), ('2', 'Không hài lòng'), ('3', 'Bình thường'), ('4', 'Hài lòng'), ('5', 'Rất hài lòng')],
        string='Đánh giá chất lượng dịch vụ')
    note = fields.Text('Ghi chú', tracking=True)
    crm_line_id = fields.Many2many('crm.line', 'line_phone_call_ref', 'phone_call', 'line', string='Service',
                                   compute='get_crm_line')
    booking_date = fields.Datetime('Booking date', tracking=True)
    call_date = fields.Datetime('Ngày gọi', default=fields.Datetime.now(), tracking=True)
    active = fields.Boolean('Hiệu lực', default=True)
    assign_time = fields.Datetime('Assign time', tracking=True, default=fields.Datetime.now())
    type_brand = fields.Selection([('hospital', 'Hospital'), ('academy', 'Academy')], string='Loại thương hiệu',
                                  related='brand_id.type')
    code_customer = fields.Char('Code customer', related='partner_id.code_customer', store=True)
    ticket_id = fields.Integer('Ticket ID')
    care_type = fields.Selection([('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'),
                                  ('DVKH', 'Dịch vụ khách hàng'), ('LT', 'Lễ tân'),
                                  ('DVKH_cs', 'Dịch vụ khách hàng - cơ sở')], 'Đơn vị chăm sóc')
    state = fields.Selection(
        [('draft', 'Chưa xử lý'), ('not_connect', 'Chưa kết nối'), ('connected', 'Đã xử lý'),
         ('later', 'Hẹn gọi lại sau'),
         ('duplicate', 'Trùng KH'), ('before', 'KH đến trước hẹn'), ('connected_1', 'Đã chăm sóc'),
         ('zalo', 'Chăm sóc qua Zalo'), ('sms', 'Gửi SMS'),
         ('not_connect_1', 'Chuyển lịch'), ('error_phone', 'Sai Số'), ('connected_2', 'Xác nhận lịch'),
         ('later_1', 'Hẹn lịch'), ('cancelled', 'Hủy lịch')],
        default='draft', string="Trạng thái", tracking=True)
    id_reexam = fields.Integer('ID reexem')
    customer_classification = fields.Selection(
        [('5', 'Khách hàng V.I.P'), ('4', 'Đặc biệt'), ('3', 'Quan tâm hơn'), ('2', 'Quan tâm'), ('1', 'Bình thường')],
        string='Phân loại khách hàng', default='1', tracking=True, compute='compute_custom_classification', store=True)
    confirm_reexam = fields.Boolean('Tạo bằng xác nhận lịch hẹn', default=False)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(PhoneCall, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone']:
                fields[field_name]['exportable'] = False

        return fields

    # @api.constrains('booking_date')
    # def validate_booking_date(self):
    #     for record in self:
    #         limited_time = record.create_date + timedelta(days=720)
    #         if record.booking_date and record.booking_date.year > limited_time.year:
    #             raise ValidationError('Giá trị ngày hẹn lịch của Booking không hợp lệ')

    @api.depends('crm_id.customer_classification')
    def compute_custom_classification(self):
        for record in self:
            record.customer_classification = False
            if record.crm_id:
                record.customer_classification = record.crm_id.customer_classification or False

    @api.depends('crm_id')
    def get_crm_line(self):
        for rec in self:
            rec.crm_line_id = [(6, 0, rec.crm_id.crm_line_ids.ids)]

    @api.onchange('phone')
    def get_partner(self):
        self.partner_id = False
        self.street = False
        if self.phone:
            self.partner_id = self.env['res.partner'].sudo().search([('phone', '=', self.phone)], limit=1).id or False

    def create_case(self):
        return {
            'name': 'Case khiếu nại',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.crm_case_view_form').id,
            'res_model': 'crm.case',
            'context': {
                'default_booking_id': self.crm_id.id,
                'default_company_id': self.company_id.id,
                'default_partner_id': self.partner_id.id,
                'default_phone_call_id': self.id,
                'default_phone': self.phone,
                'default_country_id': self.country_id.id,
                'default_state_id': self.state_id.id,
                'default_street': self.street,
                'default_brand_id': self.brand_id.id,
                'default_account_facebook': self.crm_id.facebook_acc,
            },
            'target': 'current',
        }

    @api.onchange('booking_date')
    def set_call_date_1(self):
        if self.booking_date:
            self.call_date = self.booking_date - relativedelta(days=+1)

    @api.onchange('type_crm_id')
    def set_name(self):
        if self.type_crm_id:
            self.name = self.type_crm_id.name
            self.subject = self.type_crm_id.name

    @api.onchange('phone')
    def set_partner(self):
        if self.phone:
            partner = self.env['res.partner'].search([('phone', '=', self.phone)])
            if partner:
                self.partner_id = partner.id
                self.country_id = partner.country_id.id
                self.state_id = partner.state_id.id
                self.street = partner.street

    def write(self, vals):
        res = super(PhoneCall, self).write(vals)
        for rec in self:
            if vals.get('state'):
                if vals.get('state') == 'not_connect' and rec.type_crm_id.id == self.env.ref(
                        'crm_base.type_phone_call_after_service_care').id:
                    script_sms = self.company_id.script_sms_id
                    for item in script_sms:
                        if item.run:
                            # gửi SMS SDV không nghe máy
                            if item.type == 'SDVKNM':
                                name = 'Khách không nghe máy - Phone Call CSSDV - %s' % self.crm_id.name
                                send_date = datetime.now()
                                content_sms = item.content.replace('[Ten_KH]', self.partner_id.name)
                                content_sms = content_sms.replace('[Location_Shop]', self.company_id.location_shop)
                                content_sms = content_sms.replace('[Ban_Do]', self.company_id.map_shop)
                                if self.company_id.health_declaration:
                                    content_sms = content_sms.replace('[Khai_Bao]', self.company_id.health_declaration)
                                if self.crm_id:
                                    content_sms = content_sms.replace('[Ma_Booking]', self.crm_id.name)
                                    content_sms = content_sms.replace('[Booking_Date]',
                                                                      self.crm_id.booking_date.strftime('%d-%m-%Y'))
                                sms = self.env['crm.sms'].sudo().create({
                                    'name': name,
                                    'partner_id': self.partner_id.id,
                                    'phone': self.phone,
                                    'company_id': self.company_id.id,
                                    'company2_id': [(6, 0, self.crm_id.company2_id.ids)] if self.crm_id else None,
                                    'crm_id': self.crm_id.id if self.crm_id else None,
                                    'send_date': send_date,
                                    'desc': content_sms,
                                })
        return res

    def action_close_phone_call_duplicate(self):
        active_ids = self.env.context.get('active_ids')
        pcs = self.env['crm.phone.call'].browse(active_ids)
        for pc in pcs:
            pc.state = 'duplicate'


class CrmSms(models.Model):
    _name = "crm.sms"
    _description = 'Crm SMS'
    _inherit = "mail.thread"

    name = fields.Char(string="Name", tracking=True)
    contact_name = fields.Char('Tên khách hàng', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Account KH', tracking=True)
    phone = fields.Char('SĐT', tracking=True)
    desc = fields.Text('Nội dung tin nhắn', tracking=True)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', tracking=True, related='company_id.brand_id',
                               store=True)
    company_id = fields.Many2one('res.company', string='Chi nhánh', tracking=True,
                                 default=lambda self: self.env.company)
    company2_id = fields.Many2many('res.company', string='Công ty share')
    crm_id = fields.Many2one('crm.lead', string='Booking liên quan', tracking=True, domain='[("type","!=","lead")]')
    send_date = fields.Datetime('Ngày gửi', default=fields.Datetime.now(), tracking=True)
    active = fields.Boolean('Hiệu lực', default=True)
    id_reexam = fields.Integer('ID reexem')

    @api.model
    def create(self, vals):
        res = super(CrmSms, self).create(vals)
        if res.crm_id and not res.phone:
            res.sudo().write({
                'phone': res.crm_id.partner_id.phone,
                'partner_id': res.crm_id.partner_id.id,
            })
        return res

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(CrmSms, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone_partner']:
                fields[field_name]['exportable'] = False

        return fields
