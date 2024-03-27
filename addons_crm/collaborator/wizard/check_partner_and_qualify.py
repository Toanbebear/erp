from odoo import models


class CheckPartnerAndQualify(models.TransientModel):
    _inherit = 'check.partner.qualify'

    def qualify(self):
        res = super(CheckPartnerAndQualify, self).qualify()
        booking = self.env['crm.lead'].search([('id', '=', res['res_id'])])
        booking.collaborator_id = self.lead_id.collaborator_id.id,
        return res
