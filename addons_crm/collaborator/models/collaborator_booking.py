from odoo import fields, models


class CollaboratorBooking(models.Model):
    _name = 'collaborator.booking'
    _description = 'Booking cộng tác viên'

    collaborator_id = fields.Many2one('collaborator.collaborator', string='Cộng tác viên', required=True)
    booking_id = fields.Many2one('crm.lead', string='Booking')

    # Kế thừa lại thông tin từ booking, không lưu vào bảng collaborator.booking
    partner_id = fields.Many2one(related='booking_id.partner_id')
    name = fields.Char('Mã booking', related='booking_id.name')
    company_id = fields.Many2one(related='booking_id.company_id')
    stage_id = fields.Many2one(related='booking_id.stage_id')
    create_on = fields.Datetime('Ngày tạo', related='booking_id.create_on')
    create_uid = fields.Many2one(related='booking_id.create_uid')
