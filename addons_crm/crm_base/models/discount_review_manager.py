from odoo import fields, api, models, _
from lxml import etree
from odoo.exceptions import ValidationError


class DiscountReviewManager(models.Model):
    _name = 'crm.discount.review'
    _description = 'Yêu cầu giảm giá sâu'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    REASON = [('1', 'Chi nhánh - KH Bảo hành'), ('2', 'Chi nhánh - KH Đối ngoại BGĐ Bệnh viện/Chi nhánh'),
              ('3', 'Chi nhánh - KH Đối ngoại Ban Tổng GĐ Tập đoàn'), ('4', 'Chi nhánh - Thuê phòng mổ'),
              ('5', 'Chi nhánh - Theo phân quyền Quản lý'), ('6', 'MKT - KH từ nguồn Seeding'),
              ('7', 'MKT - KH trải nghiệm dịch vụ'), ('8', 'MKT - KH đồng ý cho dùng hình ảnh truyền thông'),
              ('9', 'MKT – Theo phân quyền Quản lý'), ('10', 'SCI - Áp dụng chế độ Người nhà/CBNV (chưa có Coupon)'),
              ('11', 'SCI - Hệ thống chưa có Coupon theo CTKM đang áp dụng'), ('12', 'Khác (Yêu cầu ghi rõ lý do)'),
              ('13', 'SCI_Chương trình thiện nguyện/Hoạt động của Tập đoàn')]

    name = fields.Text('Ghi chú', tracking=True)
    reason = fields.Selection(REASON, string='Lý do xin giảm')
    type = fields.Selection([('booking', 'Dịch vụ'), ('so', 'Sản phẩm')], string='Loại phiếu',
                            default='booking', tracking=True)
    crm_line_id = fields.Many2one('crm.line', string='Dòng dịch vụ', tracking=True)
    booking_id = fields.Many2one('crm.lead', string='Booking', tracking=True)
    currency_id = fields.Many2one('res.currency', tracking=True, string='Tiền tệ')
    order_id = fields.Many2one('sale.order', string='Sale Order', tracking=True)
    order_line_id = fields.Many2one('sale.order.line', string='Sale Order line', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    type_discount = fields.Selection([('discount_pr', 'Discount percent'), ('discount_cash', 'Discount cash')],
                                     string='Type discount', tracking=True)
    discount = fields.Float('Discount', digits=(3, 0), tracking=True)
    stage_id = fields.Selection([('offer', 'Đề xuất'), ('approve', 'Đã duyệt'), ('refuse', 'Đã hủy')], string='Trạng thái',
                                default='offer', tracking=True)
    color = fields.Integer('Color Index', default=0, tracking=True)
    company_id = fields.Many2one('res.company', string='Chi nhánh', store=True, tracking=True)
    rule_discount_id = fields.Many2one('crm.rule.discount', string='Discount limit', tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    total_amount = fields.Monetary('Tổng tiền ban đầu')
    total_amount_before_deep_discount = fields.Monetary('Tổng tiền trước khi duyệt giảm giá sâu')
    total_amount_after_discount = fields.Monetary('Tổng tiền sau giảm',
                                                  compute='_compute_total_amount_after_discount', store='True', tracking=True)
    total_discount_cash = fields.Monetary('Giảm quy ra tiền mặt', compute='calculate_total_discount_cash', store=True,
                                          help='Quy đổi số giảm ra tiền mặt', tracking=True)
    user_approve = fields.Many2one('res.users', 'Người duyệt', tracking=True)
    user_refuse = fields.Many2one('res.users', 'Người hủy', tracking=True)
    note_refuse = fields.Text('Lý do hủy', tracking=True)

    @api.constrains('total_amount_after_discount')
    def validate_total_amount_after_discount(self):
        for record in self:
            if record.total_amount_after_discount < 0:
                raise ValidationError('Tổng tiền sau giảm không được âm')

    @api.depends('crm_line_id', 'total_amount_after_discount')
    def calculate_total_discount_cash(self):
        for record in self:
            record.total_discount_cash = 0
            if record.type == 'booking' and record.crm_line_id:
                if record.type_discount == 'discount_pr':
                    record.total_discount_cash = record.crm_line_id.total_before_discount * (record.discount / 100)
                elif record.type_discount == 'discount_cash':
                    record.total_discount_cash = record.discount
            elif record.type == 'so' and record.order_id and record.order_line_id:
                if record.type_discount == 'discount_pr':
                    order_line = record.order_line_id
                    total_before_discount = order_line.uom_price * order_line.product_uom_qty * order_line.price_unit
                    record.total_discount_cash = total_before_discount * (record.discount / 100)
                elif record.type_discount == 'discount_cash':
                    record.total_discount_cash = record.discount

    @api.depends('discount', 'booking_id', 'crm_line_id', 'order_id', 'order_line_id')
    def _compute_total_amount_after_discount(self):
        for record in self:
            record.total_amount_after_discount = 0
            if record.discount and record.booking_id and record.crm_line_id and record.type == 'booking':
                record.total_amount_after_discount = record.crm_line_id.total - record.total_discount_cash
            elif record.discount and record.order_id and record.order_line_id and record.type == 'so':
                for line in record.order_id.order_line:
                    if line.id == record.order_line_id.id and line.price_subtotal != 0:
                        if record.type_discount == 'discount_pr':
                            record.total_amount_after_discount = line.price_subtotal - (
                                    line.price_subtotal * (record.discount / 100))
                        elif record.type_discount == 'discount_cash':
                            record.total_amount_after_discount = line.price_subtotal - record.discount

    def approve(self):
        user_access = self.env['res.users']
        if self.rule_discount_id:
            user_access += self.rule_discount_id.user_ids
        if self.env.user not in user_access:
            raise ValidationError('Bạn không có quyền duyệt phiếu cho mức giảm giá này!!! \n' 
                                  'Để tìm hiểu chi tiết về danh sách user được duyệt, vui lòng truy cập vào mục:\n QUY TẮC GIẢM GIÁ SÂU!!!')

        if self.rule_discount_id and (self.env.user in user_access) and self.type == 'booking':
            for rec in self.crm_line_id:
                # if self.type_discount == 'discount_pr':
                #     rec.discount_percent += self.discount
                # elif self.type_discount == 'discount_cash':
                #     rec.discount_cash += self.discount
                rec.other_discount += self.total_discount_cash
                # Nếu line dịch vụ này ở trạng thái đang xử lý, cần cập nhật lại tiền của SO và cập nhật trạng thái của line dịch vụ là đang xử trí
                order_id = self.env['sale.order'].search(
                    [('booking_id', '=', self.booking_id.id), ('state', '=', 'draft')])
                order_line_id = self.env['sale.order.line']
                if order_id:
                    order_line_ids = order_id.mapped('order_line')
                    order_line_id += order_line_ids.filtered(lambda l: l.crm_line_id == rec)
                    if order_line_id and ((rec.uom_price * rec.quantity) != 0):
                        order_line_id.other_discount = (rec.other_discount / (rec.quantity * rec.uom_price)) * order_line_id.uom_price
                    rec.stage = 'processing'
            self.stage_id = 'approve'
            self.color = 4
            self.user_approve = self.env.user.id
            self.crm_line_id.discount_review_id = self.id
            self.crm_line_id.stage = 'new'
        elif self.rule_discount_id and (self.env.user in user_access) and self.type == 'so' and self.order_line_id:
            if self.type_discount == 'discount_pr':
                self.order_line_id.discount += self.discount
            elif self.type_discount == 'discount_cash':
                self.order_line_id.discount_cash += self.discount
            self.stage_id = 'approve'
            self.user_approve = self.env.user.id
            self.crm_line_id.discount_review_id = self.id
        elif not self.rule_discount_id:
            raise ValidationError('Không thể duyệt giảm giá khi không có quy tắc giảm giá !!!')

    def refuse(self):
        user_access = self.env['res.users']
        user_access += self.create_uid
        if self.rule_discount_id:
            user_access += self.rule_discount_id.user_ids
        if self.env.user not in user_access:
            raise ValidationError('Bạn không có quyền từ chối phiếu này!!!')
        else:
            self.ensure_one()
            return {
                'name': _('Nhập lý do hủy duyệt giảm giá sâu'),  # label
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('crm_base.view_form_discount_review_manager_note_refuse').id,
                'res_model': 'crm.discount.review',
                'res_id': self.id,
                'target': 'new',  # if you want popup
            }

    def add_note_refuse(self):
        self.user_refuse = self.env.user.id
        self.stage_id = 'refuse'
        if self.crm_line_id:
            self.crm_line_id.stage = 'new'
            self.crm_line_id.discount_review_id = False

    def name_get(self):
        result = []
        for rec in self:
            name = ''
            if rec.type_discount and rec.discount and rec.stage_id:
                if rec.type_discount == 'discount_pr':
                    name = 'Giảm thêm %s' % int(rec.discount) + '%'
                elif rec.type_discount == 'discount_cash':
                    name = 'Giảm thêm %s VND' % int(rec.discount)
            result.append((rec.id, name))
        return result


class RuleDiscount(models.Model):
    _name = 'crm.rule.discount'
    _description = 'Rule Discount'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', tracking=True)
    discount = fields.Float('ceiling level', tracking=True)
    discount2 = fields.Float('Maximum levels', tracking=True)
    user_ids = fields.Many2many('res.users', string='User approve', tracking=True)
    active = fields.Boolean('Active', default=True)
    _sql_constraints = [
        ('name_discount', 'unique(discount,discount2)', "Mức giảm giá này đã tồn tại"),
    ]

    @api.onchange('discount', 'discount2')
    def set_name(self):
        self.name = False
        if self.discount:
            self.name = '%s' % self.discount + '% <= MỨC GIẢM <= ' + '%s' % self.discount2 + '%'

    @api.constrains('discount')
    def condition_discount(self):
        for rec in self:
            if rec.discount <= 0:
                raise ValidationError('Mức giảm giá tối thiểu phải lớn hơn 0')
            if rec.discount >= rec.discount2:
                raise ValidationError('Mức giảm giá tối đa phải lớn hơn mức giảm giá tối thiểu')

    @api.constrains('discount2')
    def condition_discount2(self):
        for rec in self:
            if rec.discount and ((rec.discount2 < rec.discount) or (rec.discount2 > 100)):
                raise ValidationError(
                    ('Mức giảm giá tối đa chỉ nhận giá trị lớn hơn %s và nhỏ hơn hoặc bằng 100') % rec.discount)
