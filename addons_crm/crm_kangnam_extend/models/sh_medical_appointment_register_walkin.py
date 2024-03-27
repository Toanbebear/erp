from odoo import fields, models, api, _


class InheritWalkin(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    def open_walkin(self):
        return {
            'name': 'Xem phiếu khám chi tiết',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_view').id,
            'res_model': 'sh.medical.appointment.register.walkin',
            'context': {},
        }


class InheritEvaluation(models.Model):
    _inherit = 'sh.medical.evaluation'

    def open_evaluation(self):
        return {
            'name': 'Xem phiếu tái khám chi tiết',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_evaluation_view').id,
            'res_model': 'sh.medical.evaluation',
            'context': {},
        }


class InheritSurgery(models.Model):
    _inherit = 'sh.medical.surgery'

    partner_id = fields.Many2one(related='patient.partner_id')

    def open_surgery(self):
        return {
            'name': 'Xem phiếu phẫu thuật chi tiết',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_surgery_view').id,
            'res_model': 'sh.medical.surgery',
            'context': {},
        }


class InheritSpecialty(models.Model):
    _inherit = 'sh.medical.specialty'

    partner_id = fields.Many2one(related='patient.partner_id')

    def open_specialty(self):
        return {
            'name': 'Xem chuyên khoa chi tiết',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_specialty_view').id,
            'res_model': 'sh.medical.specialty',
            'context': {},
        }
