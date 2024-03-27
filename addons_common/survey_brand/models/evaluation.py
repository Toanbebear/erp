from odoo import models, fields


class MedicalEvaluation(models.Model):
    _inherit = 'sh.medical.evaluation'

    survey_answer_ids = fields.One2many('survey.user_input', 'evaluation_id', string='Lịch sử khảo sát')

    def survey_brand_evaluation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Start Survey",
            'target': 'new',
            'url': '/survey_brand/evaluation/%s' % (self.id)
        }

        # Nếu khách hàng đã khảo sát thì thông báo và không cho khảo sát nữa
        survey_user_inputs = self.env['survey.user_input'].search(
            [('evaluation_id', '=', self.id), ('state', '=', 'done')])
        if survey_user_inputs and survey_user_inputs[0]:
            survey_user_input = survey_user_inputs[0]
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = "Phiếu tái khám %s đã được khảo sát bởi %s vào lúc %s." % (self.name,
                                                                                            survey_user_input.create_uid.partner_id.name,
                                                                                            survey_user_input.create_date,
                                                                                            )
            return {
                'name': '<i class="fa fa-warning"></i> Thông báo',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view_id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
            }

        survey = self.institution.brand.survey_id
        if survey:
            return {
                'type': 'ir.actions.act_url',
                'name': "Start Survey",
                'target': 'new',
                'url': '/survey_brand/evaluation/%s/%s' % (self.id, survey.access_token)
            }
        else:
            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = 'Chưa cấu hình khảo sát cho thương hiệu'
            return {
                'name': '<i class="fa fa-warning"></i> Thông báo',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view_id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
            }
