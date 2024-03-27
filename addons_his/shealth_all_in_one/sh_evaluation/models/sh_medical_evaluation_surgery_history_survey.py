from odoo import api, fields, models


class SHealthEvaluationSurgeryHistorySurvey(models.Model):
    _name = "sh.medical.evaluation.surgery.history.survey"
    _description = "Khảo sát sau phẫu thuật"
    _inherits = {
        'sh.medical.evaluation.surgery.history': 'evaluation_surgery_history_id'
    }

    SATISFACTION_LEVEL = [('1', 'Rất hài lòng'), ('2', 'Hài lòng'), ('3', 'Bình thường'), ('4', 'Không hài lòng'),
                          ('5', 'Rất không hài lòng'), ('6', 'Bảo hành'), ('7', '')]
    DOCTOR_ATTITUDE = [('1', 'Rất hài lòng'), ('2', 'Hài lòng'), ('3', 'Bình thường'), ('4', 'Không hài lòng'),
                       ('5', 'Rất không hài lòng'), ('6', '')]

    satisfaction_level = fields.Selection(SATISFACTION_LEVEL, string='Mức độ hài lòng', default='2')
    doctor_attitude = fields.Selection(DOCTOR_ATTITUDE, string='Thái độ BSPT', default='2')
    sh_evaluation_surgery_id = fields.Many2one('sh.medical.evaluation', 'Tái khám')
    evaluation_surgery_history_id = fields.Many2one('sh.medical.evaluation.surgery.history',
                                                    string='Related Evaluation Surgery',
                                                    ondelete="cascade", required=True)

    @api.onchange('sh_evaluation_surgery_id')
    def get_domain_field(self):
        if self.sh_evaluation_surgery_id:
            walkin = self.sh_evaluation_surgery_id.walkin
            if walkin.surgeries_ids:
                list_surgery = walkin.surgeries_ids
                vals_doctor = []
                for surgery in list_surgery:
                    vals_doctor += surgery.surgery_team.mapped('team_member').ids
                return {'domain': {'service_performances': [('id', 'in', walkin.service.ids)],
                                   'main_doctor': [('id', 'in', vals_doctor)],
                                   'sub_doctor': [('id', 'in', vals_doctor)]}}
            else:
                doctor = self.env['sh.medical.physician'].search([('is_pharmacist', '=', False)])
                return {'domain': {'service_performances': [('id', 'in', self.sh_evaluation_surgery_id.services.ids)],
                                   'main_doctor': [('id', 'in', doctor.ids)],
                                   'sub_doctor': [('id', 'in', doctor.ids)]}}
