from odoo import models, fields
from odoo.exceptions import ValidationError


class UpdateLoyalty(models.TransientModel):
    _name = "update.loyalty"
    _description = 'Cập nhật thông tin loyalty'

    loyalty = fields.Many2one('crm.loyalty.card')
    amount = fields.Float('Tổng tiền đã sử dụng trên CRM')
    date_interaction = fields.Date('Ngày tương tác gần nhất')

    def confirm(self):
        if not self.loyalty:
            raise ValidationError('Lỗi hệ thống. Liên hệ Admin để xử lý.')
        else:
            self.loyalty.amount_crm = self.amount
            self.env.cr.execute("""
                SELECT SUM(amount_total) AS total_amount
                FROM sale_order
                WHERE state in ('sale', 'done') AND partner_id = %s AND brand_id = %s;""" % (
                self.loyalty.partner_id.id, self.loyalty.brand_id.id))
            sum = self.env.cr.fetchall()
            sum = sum[0][0]
            if sum:
                self.loyalty.amount = sum + self.amount
            else:
                self.loyalty.amount = self.amount
            self.loyalty.date_interaction = self.date_interaction
