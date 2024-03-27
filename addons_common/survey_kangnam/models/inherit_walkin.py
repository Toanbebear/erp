from odoo import models


class InheritLead(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    def survey_walkin(self):
        if self.booking_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

            return {
                "type": "ir.actions.act_url",
                "url": "%s/survey/start/%s/walkin_id=%s" % (base_url, self.booking_id.survey_id.access_token, self.id),
                "target": "new"
            }
