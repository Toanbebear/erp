from odoo import fields, api, models, _


class UpdateServiceWalkin(models.TransientModel):
    _name = 'update.service.walkin'

    service_room = fields.Many2one('sh.medical.health.center.ot', string='Service room')
    crm_line_ids = fields.Many2many('crm.line', string='Consulting Services')
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin',string='Walkin')
    booking_id = fields.Many2one('crm.lead',string='Booking')

