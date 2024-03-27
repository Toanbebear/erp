from odoo import fields, api, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError
from datetime import datetime, date
from odoo.tools import pycompat
import random
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
import random
import string


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


class CRMProgramVoucher(models.Model):
    _name = 'crm.voucher.program'
    _description = 'CRM voucher program'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _sql_constraints = [
        ('name_prefix', 'unique(prefix)', "Tiền tố này đã tồn tại"),
    ]

    name = fields.Char('Name')
    type_voucher = fields.Selection(
        [('discount_invoice', 'Giảm giá trên tổng hóa đơn'), ('discount_service', 'Giảm giá trên dịch vụ'), ('discount_product', 'Giảm giá trên sản phẩm')],
        string='Loại voucher', default='discount_service')
    start_date = fields.Date('Start date', tracking=True)
    end_date = fields.Date('End date', tracking=True)
    prefix = fields.Char('Tiền tố', tracking=True)
    quantity = fields.Integer('Quantity', default=1, tracking=True)
    stage_prg_voucher = fields.Selection([('new', 'Mới'), ('active', 'Đang chạy'), ('expire', 'Hết hạn')],
                                         compute="set_stage", string='Stage', default='new', store=True, tracking=True)
    active = fields.Boolean('Active', default=True)
    brand_id = fields.Many2one('res.brand', string='Brand', default=lambda self: self.env.company.brand_id,
                               tracking=True)
    company_id = fields.Many2many('res.company', string='Branch',
                                  domain="[('brand_id','=',brand_id)]", tracking=True)
    current_number_voucher = fields.Integer('Current number voucher')
    loyalty_active = fields.Boolean('Loyalty active')
    campaign_id = fields.Many2one('utm.campaign', string='Campaign',
                                  domain="[('brand_id','=',brand_id), ('campaign_status','!=','3')]",
                                  tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    price = fields.Monetary('Price', digit=(3, 0), tracking=True)
    create_on = fields.Datetime('Create on', default=fields.Datetime.now(), tracking=True)
    create_by = fields.Many2one('res.users', string='Create by', default=lambda self: self.env.user, tracking=True)
    TYPE_DISCOUNT_INVOICE = [('1', 'Giảm tiền mặt'), ('2', 'Giảm phần trăm')]
    type_discount_invoice = fields.Selection(TYPE_DISCOUNT_INVOICE, string='Loại Giảm')
    apply_for = fields.Selection([('product', 'Sản phẩm'), ('service', 'Dịch vụ')], string='Áp dụng cho ...',
                                 default='service')
    voucher_program_list = fields.One2many('crm.voucher.program.list', 'voucher_program')
    voucher_program_discount_invoice = fields.One2many('crm.voucher.program.discount.invoice', 'voucher_program')
    product_cate_ids = fields.Many2many('sh.medical.health.center.service.category', 'service_cate_voucher_program_rel',
                                        'service_cate_ids', 'voucher_program_ids', 'Nhóm dịch vụ')
    product_ids = fields.Many2many('product.product', 'product_voucher_program_rel',
                                   'product_ids', 'voucher_program_ids', string='Dịch vụ')
    country_id = fields.Many2one('res.country', default=241)
    state_ids = fields.Many2many('res.country.state', 'country_state_voucher_program_rel', 'country_state_ids',
                                 'voucher_program_ids', 'Thành phố áp dụng')
    invoice_cate_ids = fields.Many2many('sh.medical.health.center.service.category', 'invoice_cate_voucher_program_rel',
                                        'invoice_cate_ids', 'voucher_program_ids', 'Nhóm dịch vụ')

    voucher_ids = fields.One2many('crm.voucher', 'voucher_program_id', string='Voucher')

    def set_new(self):
        self.stage_prg_voucher = 'new'

    def set_active(self):
        self.stage_prg_voucher = 'active'

    def set_expire(self):
        self.stage_prg_voucher = 'expire'

    def voucher_program_renew(self):
        voucher_program = self.env['crm.voucher.program'].create({
            'name': 'GIA HẠN - ' + self.name,
            'brand_id': self.brand_id.id,
            'company_id': [(6, 0, self.company_id.ids)],
            'apply_for': self.apply_for,
            'type_voucher': self.type_voucher,
            'type_discount_invoice': self.type_discount_invoice,
            'quantity': self.quantity,
            'price': self.price,
            'loyalty_active': self.loyalty_active,
            'country_id': self.country_id.id,
            'state_ids': [(6, 0, self.state_ids.ids)],
            'product_cate_ids': [(6, 0, self.product_cate_ids.ids)],
            'product_ids': [(6, 0, self.product_ids.ids)]
        })
        if self.voucher_program_discount_invoice:
            for line in self.voucher_program_discount_invoice:
                self.env['crm.voucher.program.discount.invoice'].create({
                    'invoice_value_minimum': line.invoice_value_minimum,
                    'discount': line.discount,
                    'voucher_program': voucher_program.id

                })
        if self.voucher_program_list:
            for line in self.voucher_program_list:
                self.env['crm.voucher.program.list'].create({
                    'gift': line.gift,
                    'type_product': line.type_product,
                    'product_ctg_id': line.product_ctg_id.id,
                    'product_id': line.product_id.id,
                    'type_discount': line.type_discount,
                    'discount': line.discount,
                    'voucher_program': voucher_program.id
                })
        return {
            'name': _('Gia hạn chương trình voucher'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_voucher.voucher_program_form_view').id,
            'res_model': 'crm.voucher.program',  # model want to display
            'target': 'current',  # if you want popup,
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': voucher_program.id
        }

    @api.onchange('brand_id', 'type_voucher')
    def onchange_brand_id(self):
        pricelist_id = self.env['product.pricelist'].sudo().search([('brand_id', '=', self.brand_id.id)])
        product_ids = self.env['product.pricelist.item'].sudo().search(
            [('pricelist_id', 'in', pricelist_id.ids)]).mapped('product_id')
        return {'domain': {'product_ids': [('id', 'in', product_ids.ids)]}}

    @api.onchange('campaign_id')
    def onchange_campaign_id(self):
        self.start_date = False
        self.end_date = False
        if self.campaign_id:
            self.start_date = self.campaign_id.start_date
            self.end_date = self.campaign_id.end_date

    @api.model
    def update_stage_voucher_program(self):
        self.env.cr.execute(""" UPDATE crm_voucher_program
                                                SET stage_prg_voucher = 'expire'
                                                WHERE stage_prg_voucher <> 'expire' and end_date < (CURRENT_DATE at time zone 'utc');""")
        self.env.cr.execute(""" UPDATE crm_voucher_program
                                                SET stage_prg_voucher = 'active'
                                                WHERE stage_prg_voucher = 'new' AND start_date <= (CURRENT_DATE at time zone 'utc') AND end_date >= (CURRENT_DATE at time zone 'utc');""")

    @api.constrains('quantity')
    def limit_quantity(self):
        for rec in self:
            if rec.quantity > 1000:
                raise ValidationError(_('The maximum amount of creation in 1 time is 1000'))

    @api.constrains('price')
    def validate_fix_price(self):
        for rec in self:
            if rec.price < 0:
                raise ValidationError(_('The Price Correction field must be greater than 0'))

    @api.depends('start_date', 'end_date')
    def set_stage(self):
        for rec in self:
            rec.stage_prg_voucher = 'new'
            if rec.start_date and rec.end_date and rec.id:
                if rec.start_date > date.today():
                    rec.stage_prg_voucher = 'new'
                elif rec.end_date >= date.today() >= rec.start_date:
                    rec.stage_prg_voucher = 'active'
                elif rec.end_date < date.today():
                    rec.stage_prg_voucher = 'expire'

    def create_code(self, prefix, quantity, code_exit):
        if prefix and quantity:
            list_code = []
            for i in range(1, quantity + 1):
                random_string = generate_random_string(6)
                code = prefix + random_string
                if code not in code_exit:
                    list_code.append(code)
            return list_code

    def check_sequence(self):
        if not self.prefix:
            raise ValidationError('Vui lòng nhập tiền tố của Voucher')
        if not self.quantity:
            raise ValidationError('Vui lòng nhập số lượng voucher cần tạo')
        code_exit = self.voucher_ids.mapped('name')
        list_code = self.create_code(self.prefix, self.quantity, code_exit)
        if list_code:
            for code in list_code:
                self.env['crm.voucher'].create({'voucher_program_id': self.id,
                                                'name': code,
                                                'stage_voucher': self.stage_prg_voucher
                                                })
                self.current_number_voucher += 1

            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = '%s Voucher đã được tạo thành công!!' % self.quantity
            return {
                'name': 'Success',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view_id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
            }

    def create_vouchers(self, sequence, quantity):
        if quantity:
            for n in range(0, self.quantity):
                self.env['crm.voucher'].create(
                    {'voucher_program_id': self.id,
                     'name': sequence._next(),
                     'stage_voucher': self.stage_prg_voucher
                     }
                )

    @api.constrains('discount')
    def error_discount_percent(self):
        for rec in self:
            if rec.discount and rec.discount > 100:
                raise ValidationError(_('Can not discount over 100 percent'))
            elif rec.discount and rec.discount < 0:
                raise ValidationError(_('There is no negative discount'))

    @api.constrains('start_date', 'end_date')
    def error_date(self):
        for rec in self:
            if rec.end_date and rec.start_date and rec.start_date > rec.end_date:
                raise ValidationError(_('Start date cannot be greater than end date'))

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CRMProgramVoucher, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                             submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
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

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res


class CRMProgramVoucherList(models.Model):
    _name = 'crm.voucher.program.list'
    _description = 'List of products in Voucher'

    voucher_program = fields.Many2one('crm.voucher.program', string='Voucher program')
    brand_id = fields.Many2one('res.brand', string='Brand', related='voucher_program.brand_id', store=True)
    gift = fields.Integer(string='Tặng')
    type_product = fields.Selection([('product', 'Product'), ('product_ctg', 'Product Category')], string='Type',
                                    default='product')
    product_id = fields.Many2one('product.product', string='Product')
    product_ctg_id = fields.Many2one('sh.medical.health.center.service.category', string='List category')
    type_discount = fields.Selection([('percent', 'Percent'), ('cash', 'Cash'), ('sale_to', 'Sale to')],
                                     string='Type Discount', default='percent')
    discount = fields.Float('Discount')

    # Chỉ hiển thị những sản phẩm/dịch vụ có trong bảng giá của thương hiệu
    @api.onchange('brand_id')
    def get_product(self):
        if self.brand_id:
            price_list_item = self.env['product.pricelist.item'].search(
                [('pricelist_id.brand_id', '=', self.brand_id.id)])
            return {'domain': {'product_id': [('id', 'in', price_list_item.mapped('product_id').ids)]}}


class CRMProgramVoucherDiscountInvoice(models.Model):
    _name = 'crm.voucher.program.discount.invoice'
    _description = 'CRM voucher program discount invoice'

    voucher_program = fields.Many2one('crm.voucher.program', string='Voucher program')
    brand_id = fields.Many2one('res.brand', string='Brand', related='voucher_program.brand_id', store=True)
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id, required=True)
    invoice_value_minimum = fields.Monetary(string='Giá trị hóa đơn đạt tối thiểu')
    discount = fields.Float('Giảm')

    @api.constrains('invoice_value_minimum', 'discount')
    def constrain_discount(self):
        for record in self:
            if record.invoice_value_minimum and (record.voucher_program.type_discount_invoice == '1') and (
                    record.invoice_value_minimum < record.discount):
                raise ValidationError('Số tiền được giảm giá không thể lớn hơn số tiền điều kiện')
            elif (record.voucher_program.type_discount_invoice == '2') and (record.discount > 100) and (
                    record.discount < 0):
                raise ValidationError('Không được giảm quá 100%')
