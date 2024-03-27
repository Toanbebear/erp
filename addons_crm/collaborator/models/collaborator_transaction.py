from odoo import fields, models, api


class CollaboratorTransaction(models.Model):
    _name = 'collaborator.transaction'
    _description = 'Chi tiết hoa hồng'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    collaborator_id = fields.Many2one('collaborator.collaborator', 'Cộng tác viên')
    contract_id = fields.Many2one('collaborator.contract', 'Hợp đồng')

    company_id = fields.Many2one('res.company', string='Công ty ký hợp đồng')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id')

    booking_id = fields.Many2one('crm.lead', string='Booking')
    sale_order = fields.Many2one('sale.order', string='Mã SO', help='Mã đơn hàng')

    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')
    service_date = fields.Date('Ngày hoàn thành', help='Ngày hoàn thành dịch vụ')
    amount_total = fields.Monetary('Tiền KH làm dịch vụ (VN)',  tracking=True)
    discount_percent = fields.Float('Hoa hồng(%)', store=True, tracking=True, digits=(3, 0))
    amount_used = fields.Monetary('Tiền hoa hồng', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ',
                                  default=lambda self: self.env.company.currency_id)
    service_id = fields.Many2one('product.product', string='Dịch vụ', tracking=True)
    company_id_so = fields.Many2one('res.company', string='Công ty KH làm dịch vụ')
    note = fields.Text('Ghi chú')
    check_transaction = fields.Boolean('Đã hủy', default=False)
    rate = fields.Monetary(string='Tỷ giá ngày', digits=(3, 0))
    amount_total_usd = fields.Float('Tiền KH làm dịch vụ (USD)', digits=(3, 0),  tracking=True)
    check_overseas = fields.Boolean('Ngoại kiều', default=False)

    def name_get(self):
        record = []
        for rec in self:
            if rec.collaborator_id:
                record.append((rec.id, rec.collaborator_id.name + '[' + rec.collaborator_id.code + ']' + " " + '[' + rec.sale_order.name + ']'))
        return record


