from odoo import fields, models, _


class SHealthEvaluationSurgeryHistory(models.Model):
    _name = "sh.medical.evaluation.surgery.history"
    _description = "Lịch sử phẫu thuật liên quan tái khám"

    name = fields.Many2one('sh.medical.evaluation', string='Tái khám')
    service_performances = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ thực hiện',
                                           help="Các dịch vụ của thành viên với vai trò này thực hiện")
    main_doctor = fields.Many2many('sh.medical.physician', 'sh_evaluation_surgery_history_main_doctor_rel',
                                   'surgery_history_id', 'main_doctor_id', string='Bác sĩ chính',
                                   help="Bác sĩ chính thực hiện dịch vụ",
                                   domain=[('is_pharmacist', '=', False)], required=True)
    sub_doctor = fields.Many2many('sh.medical.physician', 'sh_evaluation_surgery_history_sub_doctor_rel',
                                  'surgery_history_id', 'sub_doctor_id', string='Bác sĩ phụ',
                                  help="Bác sĩ phụ hỗ trợ thực hiện dịch vụ",
                                  domain=[('is_pharmacist', '=', False)])
    surgery_date = fields.Datetime(string='Ngày phẫu thuật')
