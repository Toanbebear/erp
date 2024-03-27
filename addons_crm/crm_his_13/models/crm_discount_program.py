from odoo import fields, models, api
from odoo.exceptions import ValidationError


class InheritCRMDiscountProgram(models.Model):
    _inherit = 'crm.discount.program'

    discount_program_list = fields.One2many('crm.discount.program.list', 'discount_program', string='List discount')
    # CTKM cộng dồn
    # related_discounts_program_ids = fields.Many2many('crm.discount.program', 'crm_discount_program_to_discount_program',
    #                                                  'discount_program', 'discount_program_related',
    #                                                  string='Related discount program',
    #                                                  domain="[('brand_id','=',brand_id)]")
    note = fields.Html('Note')
    create_on = fields.Datetime('Create on', default=fields.Datetime.now(), tracking=True)
    create_by = fields.Many2one('res.users', string='Create by', default=lambda self: self.env.user, tracking=True)

    def open_program_renewal(self):
        return {
            'name': 'Gia hạn Coupon',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_his_13.view_form_program_renewal').id,
            'res_model': 'crm.program.renewal',
            'context': {
                'default_coupon_id': self.id,
                'default_brand_id': self.brand_id.id,
            },
            'target': 'new',
        }

    @api.model
    def update_stage_prg(self):
        self.env.cr.execute(""" UPDATE crm_discount_program
                                SET stage_prg = 'expire'
                                WHERE stage_prg <> 'expire' and end_date < (CURRENT_DATE at time zone 'utc');""")
        self.env.cr.execute(""" UPDATE crm_discount_program
                                        SET stage_prg = 'active'
                                        WHERE stage_prg = 'new' AND start_date <= (CURRENT_DATE at time zone 'utc') 
                                                                AND end_date >= (CURRENT_DATE at time zone 'utc');""")
        # if self.env['ir.config_parameter'].sudo().get_param('web.base.url') == 'https://erp.scigroup.com.vn':
        #     url = "https://api.telegram.org/bot6480280702:AAEQfjmvu6OudkToWg2jxtEmigGSY7J3ljA/sendMessage?chat_id=-4035923819&text=Đã chạy cron 'Cập nhật trạng thái Coupon'"
        #     payload = {}
        #     headers = {}
        #     requests.request("GET", url, headers=headers, data=payload)

    # @api.constrains('discount_program_list')
    # def constrain_product_and_ctg_product(self):
    #     if self.brand_id.type == 'hospital' and self.discount_program_list:
    #         product_ids = self.discount_program_list.mapped('product_id')
    #         service_ids = self.env['sh.medical.health.center.service'].search([('product_id', 'in', product_ids.ids)])
    #         for service in service_ids:
    #             if service.service_category in self.discount_program_list.mapped('product_ctg_id'):
    #                 raise ValidationError('Trùng nhóm dịch vụ')


class CRMPromotionProgramList(models.Model):
    _name = 'crm.discount.program.list'
    _description = 'CRM Promotion Program List'
    _rec_name = 'combo_note'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    COUPON_TYPE = [('1', 'Coupon đơn lẻ'), ('2', 'Coupon áp dụng cho đơn hàng'), ('3', 'Coupon cho combo dịch vụ'),
                   ('4', 'Coupon cho liệu trình'), ('5', 'Coupon cho nhóm khách hàng'), ('6', 'Coupon cho hạng thẻ'),
                   ('7', 'Coupon cho khách hàng mới/cũ'), ('8', 'Coupon cho dịch vụ đã sử dụng')]

    combo_note = fields.Char(string='Mô tả')
    discount_program = fields.Many2one('crm.discount.program', string='Discount Program',
                                       domain=[('stage_prg', 'in', ['new', 'active'])], tracking=True)
    coupon_type = fields.Selection(COUPON_TYPE, string='Loại Coupon', related='discount_program.coupon_type')
    discount_program_stage = fields.Selection(related='discount_program.stage_prg', store=True)
    check_switch = fields.Boolean('Check switch')
    brand_id = fields.Many2one('res.brand', string='Brand', related='discount_program.brand_id', store=True,
                               tracking=True)
    index = fields.Integer('Index', default='0', tracking=True)
    used = fields.Boolean('Used', default=False, tracking=True)
    type_product = fields.Selection([('product', 'Product'), ('product_ctg', 'Product Category')], string='Type',
                                    default='product', tracking=True)
    type_product_used = fields.Selection([('product', 'Product'), ('product_ctg', 'Product Category')],
                                         string='Type (Used)',
                                         default='product', tracking=True)
    type_discount = fields.Selection([('percent', 'Percent'), ('cash', 'Cash'), ('sale_to', 'Sale to')],
                                     string='Type Discount', default='percent', tracking=True)
    incremental = fields.Boolean('Incremental?', default=True, tracking=True)
    not_incremental_coupon = fields.Many2many('crm.discount.program', string='Coupon not incremental')
    gift = fields.Integer('Gift', tracking=True)
    product_ids = fields.Many2many('product.product', 'product_ids', 'product_id', string='Product')
    product_ctg_ids = fields.Many2many('sh.medical.health.center.service.category', 'service_categ_prg_rel',
                                       'discount_prg_list_id', 'service_categ_id', string='List category',
                                       tracking=True)
    product_used_ids = fields.Many2many('product.product', 'product_used_ids', 'product_id', string='Product used')
    product_ctg_used_ids = fields.Many2many('sh.medical.health.center.service.category', 'service_categ_prg_used_rel',
                                            'discount_prg_list_id', 'service_categ_id',
                                            string='List category used', tracking=True)
    discount = fields.Float('Discount', tracking=True)
    dc_min_qty = fields.Integer('Min Quantity', default=1, tracking=True)
    dc_max_qty = fields.Integer('Max Quantity', default=1, tracking=True)
    required_combo = fields.Boolean('Required combo', default=True, tracking=True)
    discount_bonus = fields.Float('Discount bonus', default=0, tracking=True)
    minimum_group = fields.Integer(string='Minimum group', default=0, tracking=True)
    create_on = fields.Datetime('Create on', default=fields.Datetime.now(), tracking=True)
    create_by = fields.Many2one('res.users', string='Create by', default=lambda self: self.env.user, tracking=True)
    group_min = fields.Integer(string='Số lượng khách tối thiểu')
    group_max = fields.Integer(string='Số lượng khách tối đa')
    limit_discount = fields.Integer(sting='Lượt áp dụng', default=999)

    @api.constrains('discount', 'type_discount')
    def constrain_percent_discount(self):
        for record in self:
            if record.type_discount == 'percent' and record.discount > 100:
                raise ValidationError('Cấu hình phần trăm giảm giá không được quá 100 %')

    @api.onchange('type_product', 'product_ids')
    def onchange_type_product_treatment(self):
        if self.discount_program.coupon_type == '4':
            # if self.type_product == 'product_ctg':
            #     raise ValidationError('Coupon liệu trình không được phép chọn nhóm dịch vụ')
            if len(self.product_ids) > 1:
                raise ValidationError('Coupon liệu trình chỉ được phép cấu hình mỗi dòng 1 dịch vụ duy nhất')

    @api.onchange('type_product')
    def onchange_type_product(self):
        if self.type_product:
            self.product_ctg_ids = None
            self.product_ids = None

    @api.onchange('product_ids', 'gift', 'discount', 'required_combo', 'incremental', 'used')
    def onchange_gift_and_product_ids(self):
        if self.gift and (len(self.product_ids) > 1):
            raise ValidationError('Bạn chỉ có thể cấu hình tặng 1 dịch vụ/ sản phẩm')
        elif self.gift and self.discount != 0:
            raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, giá trị giảm phải bằng 0')
        elif self.gift and self.required_combo:
            raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, Không thể đánh dấu combo bắt buộc')
        elif self.gift and self.incremental:
            raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, Không thể đánh dấu cộng dồn')
        elif self.gift and self.used:
            raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, Không thể đánh dấu ĐÃ SỬ DỤNG')
        elif self.gift and self.type_product == 'product_ctg':
            raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, Không thể tặng theo nhóm sản phẩm')

    @api.constrains('product_ids', 'gift', 'discount', 'required_combo', 'incremental', 'used')
    def constrains_gift_and_product_ids(self):
        for record in self:
            if record.gift and (len(record.product_ids) > 1):
                raise ValidationError('Bạn chỉ có thể cấu hình tặng 1 dịch vụ/ sản phẩm')
            elif record.gift and record.discount != 0:
                raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, giá trị giảm phải bằng 0')
            elif record.gift and record.required_combo:
                raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, Không thể đánh dấu combo bắt buộc')
            elif record.gift and record.incremental:
                raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, Không thể đánh dấu cộng dồn')
            elif record.gift and record.used:
                raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, Không thể đánh dấu ĐÃ SỬ DỤNG')
            elif record.gift and record.type_product == 'product_ctg':
                raise ValidationError('Cấu hình tặng dịch vụ/sản phẩm, Không thể tặng theo nhóm sản phẩm')


@api.onchange('discount_bonus', 'discount')
def onchange_discount(self):
    if self.discount:
        self.discount_bonus = False
    if self.discount_bonus:
        self.discount = False


@api.constrains('gift')
def constrains_gift(self):
    for record in self:
        if record.gift and record.product_ids and len(record.product_ids) > 1:
            raise ValidationError('Mỗi lần chỉ được tặng 1 dịch vụ')
        if record.gift and record.product_ctg_ids:
            raise ValidationError('Không thể tặng quà làm một nhóm dịch vụ')


@api.onchange('gift', 'used', 'incremental')
def onchange_used(self):
    if self.used:
        self.required_combo = False


@api.onchange('brand_id')
def get_product(self):
    if self.brand_id:
        price_list_item = self.env['product.pricelist.item'].search(
            [('pricelist_id.brand_id', '=', self.brand_id.id)])
        return {'domain': {'product_ids': [('id', 'in', price_list_item.mapped('product_id').ids)]}}


@api.constrains('dc_min_qty', 'dc_max_qty')
def constrain_dc_qty(self):
    for record in self:
        if record.dc_min_qty and record.dc_max_qty and record.dc_min_qty > record.dc_max_qty:
            raise ValidationError('Số lượng tối thiểu không thể lớn hơn số lượng tối đa !!!')
        if record.dc_min_qty <= 0:
            raise ValidationError('Số lượng tối thiểu phải lớn hơn 0')
        if record.dc_max_qty < 0:
            raise ValidationError('Số lượng tối đa phải lớn hơn 0')


@api.constrains('group_min', 'group_max')
def constrain_num_person(self):
    for record in self:
        if record.group_min and record.group_max and record.group_min > record.group_max:
            raise ValidationError('Số lượng khách tối thiểu không thể lớn hơn số lượng tối đa !!!')
        if record.group_min < 0:
            raise ValidationError('Số lượng khách tối thiểu phải lớn hơn 0')
        if record.group_max < 0:
            raise ValidationError('Số lượng khách tối đa phải lớn hơn 0')


class CRMPromotionProgramRule(models.Model):
    _name = 'crm.discount.program.rule'
    _description = 'CRM Promotion Program Rule'
    _rec_name = 'product_id'

    # Todo: Bỏ model này
    type = fields.Selection([('independent_service', 'Independent service'), ('affiliate_service', 'Affiliate service')]
                            , string='Type rule')
    type_discount = fields.Selection([('percent', 'Percent'), ('cash', 'Cash'), ('sale_to', 'Sale to')],
                                     string='Type Discount', default='percent')
    # product_ids = fields.Many2many('product.product', 'product_promotion_program_ref', 'program_id', 'product',
    #                                string='List product',
    #                                domain="[('type_product_crm','in',('service_crm', 'course'))]")
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('type_product_crm','in',('service_crm', 'course'))]")
    # product_ctg_ids = fields.Many2many('product.category', 'ctg_promotion_program_ref', 'program_id', 'ctg',
    #                                    string='List category')
    discount = fields.Float('Discount')
    quantity = fields.Integer('Quantity')
