from odoo import models


class InheritCRMConvertServiceGuarantee(models.TransientModel):
    _inherit = 'crm.convert.service.guarantee'

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


class InheritBookingGuarantee(models.TransientModel):
    _inherit = 'crm.create.guarantee'

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