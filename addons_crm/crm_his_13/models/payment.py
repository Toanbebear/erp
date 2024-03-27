from odoo import fields, models


class Payment(models.Model):
    _inherit = 'account.payment'

    type_brand = fields.Selection(related='brand_id.type')
    state = fields.Selection(
        [('draft', 'Draft'), ('posted', 'Validated'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),
         ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status", tracking=True)

    # def cancel(self):
    #     res = super(Payment, self).cancel()
    #     # Nếu có phiếu khám mới thực hiện hành động
    #     if self.walkin:
    #         walkin = self.walkin
    #         # Phiếu khám ĐANG THỰC HIỆN, sẽ chuyển về trạng thái khám để tính toán lại tiền có đủ để thực hiện không
    #         if walkin.state == 'InProgress':
    #             self.walkin.write({
    #                 'state': 'Scheduled'
    #             })
    #         # PHIẾU KHÁM HOÀN THÀNH sẽ không cho hủy
    #         elif walkin.state == 'Completed':
    #             raise ValidationError('Bạn không thể hủy Phiếu thu nếu phiếu khám đã hoàn thành')
    #     return res
