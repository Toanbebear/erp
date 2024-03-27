from odoo import fields, models, api


class StatementService(models.Model):
    _inherit = 'statement.service'

    service_ids = fields.Many2many('sh.medical.health.center.service', 'statement_service_rel', 'statement_id',
                                   'service_ids', string='Dịch vụ')

    @api.onchange('booking_id')
    def get_service(self):
        if self.booking_id:
            service_ids = self.booking_id.crm_line_ids.mapped('service_id')
            return {'domain': {'service_ids': [('id', '=', service_ids.ids)]}}

    # @api.onchange('service_ids')
    # def get_product_ids(self):
    #     self.product_ids = [(6, 0, self.service_id.mapped('product_id').ids)]
