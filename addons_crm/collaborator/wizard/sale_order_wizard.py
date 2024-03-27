from calendar import monthrange
from datetime import date, datetime

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class CollaboratorSaleOrderWizard(models.TransientModel):
    _name = 'collaborator.sale.order.wizard'
    _description = 'Cập nhật tiền cho ctv'

    collaborator_id = fields.Many2one('collaborator.collaborator', string="Cộng tác viên")
    source_id = fields.Many2one('utm.source', string='Nguồn',)
    sale_order = fields.Many2one('sale.order', string="SO")
    booking_id = fields.Many2one('crm.lead', string='Booking')
    company_id = fields.Many2one('res.company', string='Công ty ký hợp đồng',)
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám',)
    contract_id = fields.Many2one('collaborator.contract', 'Hợp đồng')

    def update(self):
        self.sale_order.action_update_transaction()
