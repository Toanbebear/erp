from odoo import fields, models, api


class CrmpaymentCtv(models.Model):
    _name = 'crm.payment.ctv'
    _description = 'Description'

    collaborators_id = fields.Many2one('crm.collaborators', 'Cộng tác viên')
    contract_id = fields.Many2one('collaborators.contract', 'Hợp đồng')
    company_id = fields.Many2one('res.company', string='Công ty')
    amount_total = fields.Monetary('Tổng tiền')
    amount_used = fields.Monetary('Tổng tiền đã chi')
    amount_remain = fields.Monetary('Tổng tiền còn lại', compute='set_amount_remain')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)


    # chuyển name

    @api.depends('amount_remain', 'amount_total')
    def set_amount_remain(self):
        for rec in self:
            # Tổng tiền còn lại = tổng tiền ban đầu - tổng tiền đã chi
            rec.amount_remain = rec.amount_total - rec.amount_used

class CrmDetailSale(models.Model):
    _name = 'crm.detail.sale'
    _description = 'Chi tiết hoa hồng'

    collaborators_id = fields.Many2one('crm.collaborators', 'Cộng tác viên')
    contract_id = fields.Many2one('collaborators.contract', 'Hợp đồng')
    company_id = fields.Many2one('res.company', string='Công ty')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id')
    booking_id = fields.Many2one('crm.lead', string='Booking')
    sale_order = fields.Many2one('sale.order', string='Mã SO')
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')
    service_date = fields.Date('Ngày hoàn thành dịch vụ')
    amount_total = fields.Monetary('Tiền KH làm dịch vụ')
    discount_percent = fields.Float('Hoa hồng(%)', store=True, tracking=True)
    amount_used = fields.Monetary('Tiền hoa hồng')
    amount_paid = fields.Monetary('Tổng tiền đã chi')
    amount_remain = fields.Monetary('Tổng tiền còn lại', compute='set_amount_remain')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    service_id = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ/Sản phẩm', tracking=True)

    @api.depends('amount_remain', 'amount_total')
    def set_amount_remain(self):
        for rec in self:
            # Tổng tiền còn lại = tổng tiền ban đầu - tổng tiền đã chi
            rec.amount_remain = rec.amount_used - rec.amount_paid


