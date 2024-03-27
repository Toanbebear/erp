from odoo import fields, models, api, _


class CrmCheckIn(models.Model):
    _inherit = 'crm.check.in'

    def view_booking(self):
        return {
            'name': 'Xem Booking',  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_kangnam_extend.crm_kangnam_crm_lead_view_form_extend').id,
            'res_model': 'crm.lead',
            'target': '_blank',
            'res_id': self.booking.id
        }