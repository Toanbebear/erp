from odoo import models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def post(self):
        if self.env.company != self.company_id:
            raise ValidationError(
                'Phiếu thu đang ở chi nhánh %s còn bạn đang ở chi nhánh %s\nVui lòng chuyển về chi nhánh %s để xác nhận phiếu thu' % (self.company_id.name, self.env.company.name, self.company_id.name))
        return super(AccountPayment, self).post()
