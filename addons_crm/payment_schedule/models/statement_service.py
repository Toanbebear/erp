from odoo import fields, models, api


class StatementService(models.Model):
    _inherit = 'statement.service'

    service_id = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ')
    scheduled_date = fields.Date('Ngày dự kiến thanh toán')

    @api.onchange('booking_id')
    def get_service(self):
        if self.booking_id:
            return {'domain': {'service_id': [('id', '=', self.booking_id.crm_line_ids.mapped('service_id').ids)]}}