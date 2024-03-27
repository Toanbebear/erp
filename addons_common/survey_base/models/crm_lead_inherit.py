from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    survey_id = fields.Many2one('survey.survey', string='Survey')

    # Cho phép người dùng tạo survey từ Booking
    def action_start_survey(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Survey",
            'target': 'new',
            'url': '/survey/start/%s/booking_id=%s' % (self.survey_id.access_token, self.id)
        }
