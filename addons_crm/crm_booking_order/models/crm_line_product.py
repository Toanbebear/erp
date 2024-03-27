from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class CRMLineProduct(models.Model):
    _name = 'crm.line.product'
    _description = 'Line Product of Booking'
    _rec_name = 'product_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    booking_id = fields.Many2one('crm.lead', string='Booking', domain="[('type','=','opportunity')]")
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company.id)
    brand_id = fields.Many2one('res.brand', string='Chi nhánh', related='company_id.brand_id')
    product_pricelist_id = fields.Many2one('product.pricelist', string='Bảng giá sản phẩm',
                                           domain="[('brand_id', '=', brand_id), ('type', '=', 'product')]")
    product_id = fields.Many2one('product.product', string='Sản phẩm', domain="[('type','=','product')]")
    price_unit = fields.Float('Đơn giá')
    product_uom = fields.Many2one('uom.uom', string='Đơn vị', related="product_id.uom_so_id")
    product_uom_qty = fields.Float('Số lượng', default=1)
    discount_percent = fields.Float('Giảm %')
    discount_cash = fields.Float('Giảm tiền mặt')
    sale_to = fields.Float('Giảm còn')
    discount_other = fields.Float('Giảm khác')
    total_before_discount = fields.Float('Tổng tiền ban đầu', compute="_calculate_total_before_discount", store=True)
    total = fields.Float('Tổng tiền phải thu', compute='_calculate_total_line', store=True)
    source_extend_id = fields.Many2one('utm.source', string='Nguồn mở rộng')
    CONSULTING_ROLE = [('1', 'Tư vấn độc lập'), ('2', 'Tư vấn đồng thời'), ('3', 'Lễ tân - CVTV cùng tư vấn'),
                       ('4', 'BS da liễu - KTV cùng tư vấn'), ('5', 'Tư vấn chính'), ('6', 'Tư vấn phụ')]
    consultants_1 = fields.Many2one('res.users', string='Tư vấn viên 1', tracking=True)
    consulting_role_1 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 1', tracking=True)
    consultants_2 = fields.Many2one('res.users', string='Tư vấn viên 2', tracking=True)
    consulting_role_2 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 2', tracking=True)
    consultants_3 = fields.Many2one('res.users', string='Tư vấn viên 3', tracking=True)
    consulting_role_3 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 3', tracking=True)
    STAGE_LINE_PRODUCT = [('new', 'Mới'), ('processing', 'Hóa đơn nháp'), ('sold', 'Hoàn thành'), ('waiting', 'Chờ phê duyệt'), ('cancel', 'Hủy')]
    stage_line_product = fields.Selection(STAGE_LINE_PRODUCT,
                                          string='Trạng thái',
                                          help="Giải thích các TRẠNG THÁI.\n\n"
                                               "\nMỚI : Sản phẩm chưa có trên Báo giá "
                                               "\nĐang xử trí : Sản phẩm đang có trên Báo giá"
                                               "\nHoàn thành : Sản phẩm đã được bán đi")
    note = fields.Char('Ghi chú')
    crm_discount_review = fields.Many2one('crm.discount.review', string='Giảm giá sâu')
    prg_ids = fields.Many2many('crm.discount.program', string='Coupon')
    date_create_so = fields.Datetime(string='Thời gian tạo hóa đơn')
    date_confirm_so = fields.Datetime(string='Thời gian xuất hàng')

    # reward_id = fields.Many2one('crm.loyalty.line.reward', string='Ưu đãi thẻ')

    ################## THÔNG TIN ORDER
    order_line = fields.Many2one('sale.order.line', string='Dòng SO')
    order = fields.Many2one('sale.order', related='order_line.order_id')
    crm_information_ids = fields.One2many('crm.information.consultant', 'crm_line_product_id', string='Thông tin tư vấn')
    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     if self.product_id and self.product_id.uom_so_id:
    #         self.product_uom = self.product_id.uom_so_id.id

    @api.depends('price_unit', 'product_uom_qty')
    def _calculate_total_before_discount(self):
        for record in self:
            record.total_before_discount = 0
            if record.price_unit and record.product_uom_qty:
                amount = record.price_unit * record.product_uom_qty
                record.total_before_discount = amount

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.product_pricelist_id = False
        product_pricelist_ids = self.env['product.pricelist'].sudo().search([('brand_id', '=', self.company_id.brand_id.id), ('type', '=', 'product')])
        if product_pricelist_ids:
            self.product_pricelist_id = product_pricelist_ids[0]

    @api.onchange('booking_id')
    def onchange_booking_id(self):
        if self.booking_id:
            list_company = self.env['res.company']
            if self.booking_id.company_id:
                list_company += self.booking_id.company_id
            if self.booking_id.company2_id:
                list_company += self.booking_id.company2_id
            return {'domain': {'company_id': [('id', 'in', list_company.ids)]}}

    @api.onchange('product_id', 'booking_id')
    def onchange_price_unit(self):
        if self.booking_id:
            if self.product_id:
                pricelist_item = self.env['product.pricelist.item'].search(
                    [('pricelist_id', '=', self.product_pricelist_id.id), ('product_id', '=', self.product_id.id)])
                if pricelist_item:
                    if self.product_id.uom_id == self.product_id.uom_so_id:
                        self.price_unit = pricelist_item.fixed_price
                    else:
                        self.price_unit = self.product_id.uom_id._compute_price(pricelist_item.fixed_price, self.product_id.uom_so_id)
                else:
                    raise ValidationError('Sản phẩm không được cấu hình trong bảng giá')

    @api.depends('price_unit', 'product_uom_qty', 'discount_percent', 'discount_cash', 'discount_other')
    def _calculate_total_line(self):
        for rec in self:
            rec.total = 0
            rec.total = rec.total_before_discount * (
                    1 - (rec.discount_percent or 0.0) / 100.0) - rec.discount_cash - rec.discount_other

    def go_to_so(self):
        if not self.order:
            raise ValidationError('Hiện tại không có báo giá nào của khách hàng gắn với sản phẩm này.')
        else:
            return {
                'name': _('Chi tiết SO'),  # label
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('sale.view_order_form').id,
                'res_model': 'sale.order',  # model want to display
                'target': 'current',  # if you want popup,
                # 'context': {},
                'res_id': self.order.id
            }

    @api.onchange('product_pricelist_id')
    def get_product_ids(self):
        self.product_id = False
        if self.product_pricelist_id:
            product_ids = self.env['product.pricelist.item'].sudo().search([('pricelist_id', '=', self.product_pricelist_id.id)])
            return {'domain': {'product_id': [('id', 'in', product_ids.mapped('product_id').ids)]}}

    def open_wizard_cancel_line_product(self):
        return {
            'name': 'HỦY DÒNG SẢN PHẨM',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_booking_order.view_form_cancel_crm_line_product').id,
            'res_model': 'crm.line.product.cancel',
            'context': {
                'default_crm_line_product_id': self.id,
            },
            'target': 'new',
        }

    @api.onchange('product_uom_qty')
    def validate_product_uom_qty(self):
        for record in self:
            if record.product_uom_qty <= 0:
                raise ValidationError('Số lượng của sản phẩm phải lớn hơn 0')

    @api.onchange('product_uom_qty')
    def validate_product_uom_qty(self):
        if self.product_uom_qty <= 0:
            raise ValidationError('Số lượng của sản phẩm phải lớn hơn 0')

