from odoo import fields, models, api


class ChangeBookingDate(models.TransientModel):
    _name = 'change.booking.date'
    _description = 'Thay đổi ngày hẹn lịch'

    booking_id = fields.Many2one('crm.lead', string='Booking')
    booking_date = fields.Datetime('Ngày hẹn lịch mới')

    def confirm(self):
        self.booking_id.booking_date = self.booking_date
