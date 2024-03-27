from odoo import models, fields, api


class PRWalkin(models.Model):
    _inherit = "sh.medical.appointment.register.walkin"

    sol_product = fields.Many2many('crm.line', compute='_compute_sol_product')
    line_done = fields.Many2many('crm.line', string='Dịch vụ kết thúc')

    @api.depends('sale_order_id')
    def _compute_sol_product(self):
        for record in self:
            record.sol_product = [(5)]
            if record.sale_order_id and record.sale_order_id.order_line:
                record.sol_product = [(6, 0, record.sale_order_id.order_line.mapped('crm_line_id').ids)]
