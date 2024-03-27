from odoo import api, fields, models
from odoo import fields, models, api, _
SOURCE_TYPE = [('online', 'Online'),
               ('offline', 'Offline')]
PAYMENT_TYPE = [
    ('tai_don_vi', 'Tại đơn vị'),
    ('thu_ho', 'Thu hộ'),
    ('chi_ho', 'Chi hộ'),
]
SERVICE_HIS_TYPE = [('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'), ('ChiPhi', 'Chi phí khác')]


class CRMSalePayment(models.Model):
    _name = 'crm.sale.payment'
    _description = 'Tổng hợp thanh toán'

    name = fields.Char(string='Tổng hợp thanh toán', readonly=True)
    booking_id = fields.Many2one('crm.lead', string="Booking", compute='_compute_booking_id', store=True)
    transfer_payment_id = fields.Many2one('crm.transfer.payment', string="Phiếu điều chuyển", ondelete='cascade')
    transfer_payment_line_id = fields.Many2one('crm.transfer.payment.line', string="Chi tiết điều chuyển", ondelete='cascade')
    account_payment_id = fields.Many2one('account.payment', string="Phiếu thu tiền", ondelete='cascade')
    account_payment_detail_id = fields.Many2one('crm.account.payment.detail', string="Chi tiết phiếu thu dịch vụ")
    account_payment_product_detail_id = fields.Many2one('crm.account.payment.product.detail',
                                                        string="Chi tiết phiếu thu sản phẩm")
    crm_line_id = fields.Many2one('crm.line', string="Line dịch vụ")
    crm_line_product_id = fields.Many2one('crm.line.product', string="Line sản phẩm")

    product_category_id = fields.Many2one('product.category', string='Nhóm dịch vụ')
    product_type = fields.Selection([('product', "Sản phẩm"), ('service', 'Dịch vụ')],
                                    string='Loại (SP/Dịch vụ)', tracking=True)

    product_id = fields.Many2one('product.product', string="Sản phẩm")
    service_id = fields.Many2one('sh.medical.health.center.service', string="Dịch vụ")
    kpi_point = fields.Float('Điểm dịch vụ', digits=(16, 2))
    payment_type = fields.Selection([('inbound', _('Nhận tiền')), ('outbound', _('Hoàn tiền')), ('transfer', _('Giao dịch nội bộ'))], string="Loại thanh toán")
    amount_proceeds = fields.Monetary(string="Số tiền giao dịch", default=0)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.company.currency_id)
    is_deposit = fields.Boolean(string="Là thanh toán đặt cọc?")
    coupon_ids = fields.Many2many('crm.discount.program', string="Chương trình giảm giá")

    # line_creator_dept = fields.Char(string="Phòng ban của người tạo line dịch vụ")
    # consultants_1_dept = fields.Char(string="Phòng ban của tư vấn viên 1")
    # consultants_2_dept = fields.Char(stKring="Phòng ban của tư vấn viên 2")
    CONSULTING_ROLE = [('1', 'Tư vấn độc lập'), ('2', 'Tư vấn đồng thời'), ('3', 'Lễ tân - CVTV cùng tư vấn'),
                       ('4', 'BS da liễu - KTV cùng tư vấn'), ('5', 'Tư vấn chính'), ('6', 'Tư vấn phụ')]
    consultants_1 = fields.Many2one('res.users', string='Consultants 1', store=True, compute='_compute_consultants')
    consulting_role_1 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 1', store=True, compute='_compute_consultants')
    consultants_2 = fields.Many2one('res.users', string='Consultants 2', store=True, compute='_compute_consultants')
    consulting_role_2 = fields.Selection(CONSULTING_ROLE, string='Vai trò tư vấn viên 2', store=True, compute='_compute_consultants')

    partner_id = fields.Many2one('res.partner', string="Khách hàng")
    user_id = fields.Many2one('res.users', string="Người hưởng hoa hồng")
    company_id = fields.Many2one('res.company', string="Chi nhánh ghi nhận doanh số")
    transaction_company_id = fields.Many2one('res.company', string='Chi nhánh liên quan')
    category_source_id = fields.Many2one('crm.category.source', string="Tên nguồn")
    create_date = fields.Date(string='Ngày tạo', readonly=True)
    source_type = fields.Selection(SOURCE_TYPE, string='Loại', related='crm_line_id.source_extend_id.type_source')
    communication = fields.Char(string='Nội dung giao dịch')
    over_discount = fields.Boolean(string='Vượt trần khuyến mãi', compute='over_discount_compute', store=True)
    internal_payment_type = fields.Selection(PAYMENT_TYPE, string='Loại giao dịch nội bộ')
    service_category = fields.Many2one('sh.medical.health.center.service.category', related='service_id.service_category', store=True)
    not_sale = fields.Boolean(string='Không tính doanh số', compute='_compute_not_sale', store=True)
    remaining_amount = fields.Monetary(string="Tiền chưa sử dụng", currency_field="currency_id", compute='_compute_remaining_amount', store=True)
    department = fields.Selection(SERVICE_HIS_TYPE, string='Phòng ban')
    payment_date = fields.Date(string='Ngày thanh toán', compute='compute_payment_date', store=True)

    booking_create_user = fields.Many2one('res.users', string='Người tạo booking', related='booking_id.create_by')

    @api.depends('crm_line_id', 'crm_line_product_id')
    def _compute_consultants(self):
        for rec in self:
            if self.crm_line_id:
                rec.consultants_1 = rec.crm_line_id.consultants_1
                rec.consulting_role_1 = rec.crm_line_id.consulting_role_1
                rec.consultants_2 = rec.crm_line_id.consultants_2
                rec.consulting_role_2 = rec.crm_line_id.consulting_role_2
            elif self.crm_line_product_id:
                rec.consultants_1 = rec.crm_line_product_id.consultants_1
                rec.consulting_role_1 = rec.crm_line_product_id.consulting_role_1
                rec.consultants_2 = rec.crm_line_product_id.consultants_2
                rec.consulting_role_2 = rec.crm_line_product_id.consulting_role_2
            else:
                rec.consultants_1 = False
                rec.consulting_role_1 = False
                rec.consultants_2 = False
                rec.consulting_role_2 = False
    @api.depends('account_payment_id.crm_id', 'transfer_payment_id.crm_id')
    def _compute_booking_id(self):
        for rec in self:
            if rec.account_payment_id.crm_id:
                rec.booking_id = rec.account_payment_id.crm_id
            elif rec.transfer_payment_id.crm_id:
                rec.booking_id = rec.transfer_payment_id.crm_id
            else:
                rec.booking_id = None

    @api.depends('account_payment_id', 'transfer_payment_id')
    def compute_payment_date(self):
        for rec in self:
            if rec.account_payment_id:
                rec.payment_date = rec.account_payment_id.payment_date
            else:
                rec.payment_date = rec.transfer_payment_id.payment_date

    @api.depends('service_id')
    def _compute_not_sale(self):
        for rec in self:
            if rec.service_id and rec.service_id.not_sale is True:
                rec.not_sale = True
            else:
                rec.not_sale = False

    @api.depends('crm_line_id', 'crm_line_product_id')
    def _compute_remaining_amount(self):
        for payment in self:
            remaining_amount = 0
            if payment.crm_line_id:
                remaining_amount = payment.crm_line_id.remaining_amount
            if payment.crm_line_product_id:
                remaining_amount = payment.crm_line_product_id.remaining_amount
            payment.remaining_amount = remaining_amount

    @api.depends('product_id', 'service_id')
    def over_discount_compute(self):
        for rec in self:
            if rec.service_id and \
                    rec.company_id.brand_id in rec.service_id.ceiling_discount_ids.brand_id and rec.crm_line_id.prg_ids:
                rec.over_discount = True
            else:
                rec.over_discount = False

    @api.model
    def create(self, vals):
        res = super(CRMSalePayment, self).create(vals)
        if self._context.get('name', _('New')) == _('New'):
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(fields.datetime.today()))
            res.name = self.env['ir.sequence'].next_by_code('crm.sale.payment', sequence_date=seq_date) or _('New')
        return res

    # check_permissions = fields.Boolean(string='Kiểm tra nhóm người dùng', compute='_compute_check_permissions')
    #
    # def _compute_check_permissions(self):
    #     for record in self:
    #         if record.user_has_groups('shealth_all_in_one.group_sh_medical_patient'):
    #             record.check_permissions = True
    #         else:
    #             record.check_permissions = False
