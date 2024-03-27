from odoo import models, fields, api
from datetime import timedelta, MAXYEAR
from odoo.exceptions import ValidationError
from datetime import timedelta


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    calendar_event = fields.One2many('calendar.event', 'opportunity_id', string='Danh sách lịch hẹn')

    def create_an_appointment(self):
        self.ensure_one()
        return {
            'name': 'Tạo lịch hẹn',
            'view_mode': 'form',
            'res_model': 'create.an.appointment',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('crm_calendar_event.form_create_calendar_event_from_booking').id,
            'context': {
                'default_customer_id': self.partner_id.id,
                'default_opportunity_id': self.id,
            },
            'target': 'new',
        }

    def create_an_appointment_surgery(self):
        self.ensure_one()
        return {
            'name': 'Tạo lịch hẹn PT',
            'view_mode': 'form',
            'res_model': 'calendar.event',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('calendar.view_calendar_event_form').id,
            'context': {
                'default_customer_id': self.partner_id.id,
                'default_opportunity_id': self.id,
                'default_is_calendar_surgery': True,
                'default_name': 'Khách hàng : %s' % self.partner_id.name
            },
            'target': 'new',
        }

    @api.onchange('booking_date')
    def change_booking_date(self):
        if self.booking_date and self.calendar_event:
            calendar_change = self._origin.calendar_event.filtered(
                lambda c: (c.start == self.booking_date) or (c.create_date == self.create_date))
            duration = calendar_change.duration
            calendar_change.write({
                'start': self.booking_date,
                'stop': self.booking_date + timedelta(hours=duration) + timedelta(seconds=1)
            })


