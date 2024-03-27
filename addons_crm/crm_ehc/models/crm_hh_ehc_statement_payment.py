from odoo import fields, models, api


class StatementPaymentEHC(models.Model):
    _name = 'crm.hh.ehc.statement.payment'
    _description = 'Payment EHC'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'invoice_code'

    booking_id = fields.Many2one('crm.lead', string='Booking')
    invoice_date = fields.Date('Ngày thanh toán')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ')
    amount_paid = fields.Monetary('Số tiền thanh toán', tracking=True)
    note = fields.Text('Ghi chú')
    invoice_code = fields.Char('Mã phiếu thu EHC')
    invoice_id = fields.Char('ID phiếu thu EHC')
    patient_code = fields.Char('Mã bệnh nhân')
    patient_name = fields.Char('Tên bệnh nhân')
    invoice_group_code = fields.Char('Sổ thu')
    invoice_status = fields.Selection([('0', 'Hoạt động'), ('1', 'Hủy')], tracking=True, string='Trạng thái')
    invoice_user = fields.Many2one('crm.hh.ehc.user', string='Người thu tiền', tracking=True)
    invoice_method = fields.Selection([('1', 'Tiền mặt'), ('2', 'Chuyển khoản'), ('3', 'Ghi nợ'), ('4', 'POS')], string='Hình thức thanh toán')
    invoice_type = fields.Selection([('1', 'Thu tiền'), ('2', 'Hoàn tiền')], string='Loại thanh toán')
    allotted = fields.Boolean('Đã phân bổ', default=False)
    patient_id = fields.Many2one('crm.hh.ehc.patient', string='Bệnh nhân')

    booking_category_source = fields.Many2one('crm.category.source', string='Nhóm nguồn Booking', related='booking_id.category_source_id', store=True)
    booking_source = fields.Many2one('utm.source', string='Nguồn Booking', related='booking_id.source_id', store=True)
    booking_phone = fields.Char('SĐT Booking', related='booking_id.phone', store=True)
    booking_create_by = fields.Many2one('res.users', string='Người tạo Booking', related='booking_id.create_by', store=True)
    booking_company = fields.Many2one('res.company', string='Chi nhánh Booking', related='booking_id.company_id', store=True)
    booking_product_category_ids = fields.Many2many('product.category', 'crm_hh_ehc_statement_prd_ctg_rel', 'statement_id', 'product_category_id', string='Nhóm dịch vụ Booking', compute='_get_product_category', store=True)

    contract_code = fields.Text('Mã hợp đồng EHC')
    payment_code_erp = fields.Text('Mã phiếu thanh toán ERP', help='Dùng cho trường hợp đặt cọc')

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(StatementPaymentEHC, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['booking_phone']:
                fields[field_name]['exportable'] = False

        return fields
    @api.depends('booking_id')
    def _get_product_category(self):
        for rec in self:
            if rec.booking_id:
                rec.booking_product_category_ids = [(6, 0, rec.booking_id.product_category_ids.ids)]


class InheritCRM(models.Model):
    _inherit = 'crm.lead'

    statement_payment_ehc_ids = fields.One2many('crm.hh.ehc.statement.payment', 'booking_id',
                                                string='Bảng kê thanh toán EHC')

    @api.depends('add_amount_paid_crm', 'payment_ids.state', 'payment_ids.payment_type', 'payment_ids.amount', 'statement_payment_ehc_ids.invoice_status', 'statement_payment_ehc_ids.invoice_type')
    def set_paid_booking(self):
        for rec in self:
            if rec.company_id.code == 'BVHH.HN.01' and rec.type == 'opportunity':
                rec.amount_paid = 0
                if rec.statement_payment_ehc_ids:
                    for payment in rec.statement_payment_ehc_ids:
                        if payment.invoice_type == '1' and payment.invoice_status == '0':
                            rec.amount_paid += payment.amount_paid
                        elif payment.invoice_type == '2' and payment.invoice_status == '0':
                            rec.amount_paid -= payment.amount_paid
            else:
                if rec.add_amount_paid_crm > 0:
                    paid = rec.add_amount_paid_crm
                else:
                    paid = 0
                if rec.payment_ids:
                    for pm in rec.payment_ids:
                        if pm.state in ['posted', 'reconciled']:
                            if pm.payment_type == 'inbound':
                                paid += pm.amount_vnd
                            elif pm.payment_type == 'outbound':
                                paid -= pm.amount_vnd
                rec.amount_paid = paid

    # amount_paid_ehc = fields.Float('Tổng tiền khách trả EHC')
    # amount_paid_ehc = fields.Float('Tổng tiền khách trả EHC', compute='_compute_amount_paid_ehc', store=True)
    #
    # @api.depends('statement_payment_ehc_ids.invoice_status', 'statement_payment_ehc_ids.invoice_type')
    # def _compute_amount_paid_ehc(self):
    #     for record in self:
    #         if record.company_id.code == 'BVHH.HN.01' and record.type == 'opportunity':
    #             if record.statement_payment_ehc_ids:
    #                 for payment in record.statement_payment_ehc_ids:
    #                     if payment.invoice_type == '1' and payment.invoice_status == '0':
    #                         record.amount_paid_ehc += payment.amount_paid
    #                     elif payment.invoice_type == '2' and payment.invoice_status == '0':
    #                         record.amount_paid_ehc -= payment.amount_paid
    #             else:
    #                 record.amount_paid_ehc = 0

    # def open_form_sale_allocation_ehc(self):
    #     return {
    #         'name': 'Phân bổ doanh số EHC',
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('crm_ehc.view_form_crm_sale_allocation_ehc').id,
    #         'res_model': 'crm.ehc.sale.allocation',
    #         'context': {
    #             'default_partner_id': self.partner_id.id,
    #             'default_booking_id': self.id,
    #         },
    #         'target': 'new'
    #     }