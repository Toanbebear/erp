from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
import json
from lxml import etree
from calendar import monthrange

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO
from datetime import datetime, date


class CRMDiscountProgram(models.Model):
    _name = 'crm.discount.program'
    _description = 'CRM Discount Program'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    COUPON_TYPE = [('1', 'Coupon đơn lẻ'), ('2', 'Coupon áp dụng cho đơn hàng'), ('3', 'Coupon cho combo dịch vụ'),
                   ('4', 'Coupon cho liệu trình'), ('5', 'Coupon cho nhóm khách hàng'), ('6', 'Coupon cho hạng thẻ'),
                   ('7', 'Coupon cho khách hàng mới/cũ'), ('8', 'Coupon cho dịch vụ đã sử dụng')]

    name = fields.Char('Name', tracking=True)
    code = fields.Char('Code', tracking=True)
    coupon_type = fields.Selection(COUPON_TYPE, string='Loại Coupon')
    start_date = fields.Date('Start date', tracking=True)
    end_date = fields.Date('End date', tracking=True)
    stage_prg = fields.Selection([('new', 'New'), ('active', 'Active'), ('expire', 'Expire')], string='Stage',
                                 compute='set_stage_prg', default='new', store=True, tracking=True)
    active = fields.Boolean('Active', default=True)
    brand_id = fields.Many2one('res.brand', string='Brand',
                               domain=lambda self: [('id', 'in', self.env.user.company_ids.mapped('brand_id').ids)],
                               tracking=True)
    company_ids = fields.Many2many('res.company', string='Company', domain="[('brand_id','=',brand_id)]", tracking=True)
    campaign_id = fields.Many2one('utm.campaign', string='Campaign', domain="[('brand_id','=',brand_id)]",
                                  tracking=True)

    # thẻ thành viên đc áp dụng cùng
    loyalty_active = fields.Boolean('Loyalty active')

    @api.onchange('campaign_id')
    def onchange_campaign_id(self):
        self.start_date = False
        self.end_date = False
        if self.campaign_id:
            self.start_date = self.campaign_id.start_date
            self.end_date = self.campaign_id.end_date

    @api.onchange('brand_id')
    def onchange_brand_id(self):
        self.campaign_id = False
        domain = [('campaign_status', '!=', '3')]
        if self.brand_id:
            domain += [('brand_id', '=', self.brand_id.id)]
        return {'domain': {'campaign_id': [('id', 'in', self.env['utm.campaign'].search(domain).ids)]}}

    def set_new(self):
        self.stage_prg = 'new'

    def set_active(self):
        self.stage_prg = 'active'

    def set_expire(self):
        self.stage_prg = 'expire'

    def write(self, vals):
        res = super(CRMDiscountProgram, self).write(vals)
        for record in self:
            if vals.get('company_ids') or vals.get('brand_id') or vals.get('start_date') or vals.get('end_date'):
                record.set_code()
        return res

    def set_code(self):
        company_code = []
        if self.company_ids:
            for company in self.company_ids:
                company_code.append(company.code)
        else:
            company_code.append('ALL')
        start_date = date(self.start_date.year, self.start_date.month, 1)
        end_date = date(self.start_date.year, self.start_date.month,
                        monthrange(self.start_date.year, self.start_date.month)[1])
        self.code = 'CTKM_' + self.brand_id.code + '_' + '.'.join(company_code) + '_' + str(self.start_date.year) + str(
            self.start_date.month) + '_' + str(self.env['crm.discount.program'].search_count(
            [('brand_id', '=', self.brand_id.id), ('start_date', '>=', start_date), ('start_date', '<=', end_date)]))
        return self.code

    @api.model
    def create(self, vals_list):
        res = super(CRMDiscountProgram, self).create(vals_list)
        res.set_code()
        return res

    # @api.onchange('type_service')
    # def change_by_type_service(self):
    #     if self.type_service == 'product':
    #         self.product_ctg_ids = False
    #     elif self.type_service == 'category':
    #         self.product_ids = False

    @api.constrains('start_date', 'end_date')
    def error_date(self):
        for rec in self:
            if rec.end_date and rec.start_date and rec.start_date > rec.end_date:
                raise ValidationError(_('Start date cannot be greater than end date'))

    @api.constrains('discount')
    def error_discount_percent(self):
        for rec in self:
            if rec.discount and rec.discount > 100:
                raise ValidationError(_('Can not discount over 100 percent'))
            elif rec.discount and rec.discount < 0:
                raise ValidationError(_('There is no negative discount'))

    @api.depends('start_date', 'end_date')
    def set_stage_prg(self):
        for rec in self:
            rec.stage_prg = 'new'
            if rec.start_date and rec.end_date and rec.id:
                if rec.end_date >= date.today() >= rec.start_date:
                    rec.stage_prg = 'active'
                elif rec.start_date > date.today():
                    rec.stage_prg = 'new'
                elif rec.end_date < date.today():
                    rec.stage_prg = 'expire'

    def unlink(self):
        for rec in self:
            if rec.stage_prg != 'new':
                raise ValidationError('Bạn không thể xóa các coupon đang không có trạng thái là mới !!!')
            return super(CRMDiscountProgram, self).unlink()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CRMDiscountProgram, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                              submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field"):
                node.set("attrs",
                         "{'readonly':[('stage_prg','in',['active','expire'])]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = "[('stage_prg','in',['active','expire'])]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='start_date']"):
                node.set("attrs", "{'readonly':[('campaign_id','!=',False)]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = "[('campaign_id','!=',False)]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='end_date']"):
                node.set("attrs", "{'readonly':[('campaign_id','!=',False)]}")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = "[('campaign_id','!=',False)]"
                node.set('modifiers', json.dumps(modifiers))

            for node in doc.xpath("//field[@name='create_on']"):
                node.set("readonly", "True")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = True
                node.set("modifiers", json.dumps(modifiers))

            for node in doc.xpath("//field[@name='create_by']"):
                node.set("readonly", "True")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = True
                node.set("modifiers", json.dumps(modifiers))

            for node in doc.xpath("//field[@name='write_date']"):
                node.set("readonly", "True")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = True
                node.set("modifiers", json.dumps(modifiers))

            for node in doc.xpath("//field[@name='write_uid']"):
                node.set("readonly", "True")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = True
                node.set("modifiers", json.dumps(modifiers))

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res



