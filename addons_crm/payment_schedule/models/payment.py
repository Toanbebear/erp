from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def post(self):
        res = super(AccountPayment, self).post()
        if self.crm_id:
            self.crm_id.update_payment_schedule()
        return res