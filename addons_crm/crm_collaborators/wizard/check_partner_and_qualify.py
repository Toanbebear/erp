
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import pytz

class CheckPartnerAndQualify(models.TransientModel):
    _inherit = 'check.partner.qualify'

    def qualify(self):
        res = super(CheckPartnerAndQualify, self).qualify()
        booking = self.env['crm.lead'].search([('id', '=', res['res_id'])])
        # booking.create({
        #     'source_ctv_id' : self.lead_id.source_ctv_id.id,
        # })
        booking.collaborators_id = self.lead_id.collaborators_id.id,
        return res
