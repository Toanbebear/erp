from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.phone.call'

    survey_answer_ids = fields.One2many('survey.user_input', 'phone_call_id', string='Lịch sử khảo sát', store=True)

    # Cho phép người dùng tạo survey từ Booking
    def action_start_survey_phone_call(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Survey",
            'target': 'new',
            'url': '/survey_brand/phone_call/%s' % self.id
        }
