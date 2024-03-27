import datetime

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        walkin = self.env['sh.medical.appointment.register.walkin'].sudo().search([('sale_order_id', '=', self.id)], limit=1)
        if walkin and walkin.line_done:
            for line in walkin.line_done:
                line.pr_done = True
                if not line.pr_date_done:
                    line.pr_date_done = datetime.date.today()
        return res

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        walkin = self.env['sh.medical.appointment.register.walkin'].sudo().search([('sale_order_id', '=', self.id)],
                                                                                  limit=1)
        if walkin and walkin.line_done:
            for line in walkin.line_done:
                line.pr_done = False
                line.pr_date_done = False
        return res