from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    def get_wc_by_analytic_account(self, analytic_account):
        wc = self.search([('costs_hour_account_id', '=', analytic_account.id)], limit=1)
        if len(wc) > 0:
            return wc
        else:
            return None