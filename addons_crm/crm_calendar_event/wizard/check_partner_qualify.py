from odoo import models, fields, api
from datetime import timedelta, MAXYEAR
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class CheckPartnerCalendarEvent(models.TransientModel):
    _inherit = 'check.partner.qualify'

    physician = fields.Many2one('sh.medical.physician', string='Bác sĩ',
                                domain="[('company_id', 'in', allowed_company_ids)]")

    def qualify(self):
        res = super(CheckPartnerCalendarEvent, self).qualify()
        booking = self.env['crm.lead'].search([('id', '=', res['res_id'])])
        _logger.info('In ra booking --------------------------------------------')
        _logger.info(booking)
        stop = booking.booking_date + timedelta(hours=2) + timedelta(seconds=1)
        partner_ids = [booking.partner_id.id, self.env.user.partner_id.id]
        services = booking.crm_line_ids.mapped('service_id')
        description = 'Khách %s mong muốn tư vấn/làm dịch vụ %s' % (
            booking.partner_id.name, ','.join(services.mapped('name')))
        event = self.env['calendar.event'].sudo().create({
            'name': description,
            'customer_id': booking.partner_id.id,
            'user_id': self.env.user.id,
            'partner_ids': [(6, 0, partner_ids)],
            'start': booking.booking_date,
            'stop': stop,
            'duration': 2,
            'physician': self.physician.id,
            'alarm_ids': [(6, 0, [self.env.ref('calendar.alarm_notif_1').id])],
            'services': [(6, 0, services.ids)] if services else False,
            'opportunity_id': booking.id if booking else False,
            'company_id': booking.company_id.id,
            'location': booking.company_id.name,
            'description': description,
        })
        _logger.info('In ra event --------------------------------------------')
        _logger.info(event)

        return res