from odoo import models


class PartnerQualify(models.TransientModel):
    _inherit = 'check.partner.qualify'

    def qualify(self):
        res = super(PartnerQualify, self).qualify()
        booking = self.env['crm.lead'].browse(int(res['res_id']))
        if booking and booking.partner_id:
            booking.day_of_birth = booking.partner_id.birth_date.day if booking.partner_id.birth_date else 1
            booking.month_of_birth = booking.partner_id.birth_date.month if booking.partner_id.birth_date else 1
        return res

    def return_booking_new(self, booking):
        return {
            'name': 'Booking',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_kangnam_extend.crm_kangnam_crm_lead_view_form_extend').id,
            'res_model': 'crm.lead',
            'res_id': booking.id,
        }