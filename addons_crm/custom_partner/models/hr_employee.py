from odoo import models, fields, api


class HrEmployeePartner(models.Model):
    _inherit = "hr.employee"

    def write(self, vals):
        res = super(HrEmployeePartner, self).write(vals)
        for record in self:
            if record.user_id and record.employee_code and record.user_id.code_customer != record.employee_code:
                record.user_id.code_customer = record.employee_code
        return res
