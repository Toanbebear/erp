from odoo import models, fields


class CalendarSelectService(models.TransientModel):
    _inherit = "crm.select.service"

    calendar_events = fields.Many2many('calendar.event', string='Lịch hẹn', domain="[('state', '=', 'confirm'), ('opportunity_id', '=', booking_id)]")

    def create_quotation(self):
        res = super(CalendarSelectService, self).create_quotation()
        if self.calendar_events:
            for record in self.calendar_events:
                record.state = 'come'
        return res


