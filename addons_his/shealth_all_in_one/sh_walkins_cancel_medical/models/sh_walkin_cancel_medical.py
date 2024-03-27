from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ShWalkinCancelMedical(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    cancel_user = fields.Many2one('res.users', string='Người Hủy')
    department_cancel_user = fields.Many2one('hr.department', string='Phòng Ban Người Hủy')
    note_cancel = fields.Char(string="Lý Do Hủy")
    date_cancel = fields.Datetime('Ngày Hủy')

    #HỦY PHIẾU KHÁM
    def set_to_cancelled_walkin(self):
        if self.specialty_ids and any(state in ['Confirmed', 'In Progress', 'Done'] for state in self.specialty_ids.mapped('state')):
            raise ValidationError('Không thể hủy phiếu khám vì phiếu chuyên khoa đã/đang được xử lý')
        elif self.surgeries_ids and any(state in ['Confirmed', 'In Progress', 'Done'] for state in self.surgeries_ids.mapped('state')):
            raise ValidationError('Không thể hủy phiếu khám vì phiếu phẫu thuật đã hoàn thành')
        if ((self.env.ref('shealth_all_in_one.group_sh_medical_stock_user') in self.env.user.groups_id)
            or (self.env.ref('shealth_all_in_one.group_sh_medical_receptionist') in self.env.user.groups_id)
            or (self.env.ref('shealth_all_in_one.group_sh_medical_manager') in self.env.user.groups_id)) or (self.env.user == self.create_uid):
            return {
                'name': 'THÔNG TIN HUỶ PHIẾU',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('shealth_all_in_one.cancel_medical_form_view').id,
                'res_model': 'cancel.medical',
                'target': 'new',
                'context': {
                    'default_cancel_user': self.env.user.id,
                    'default_walkin_id': self.id,
                }
            }
        else:
            raise ValidationError('Chỉ USER TẠO PHIẾU hoặc TRƯỞNG BỘ PHẬN mới có quyền hủy phiếu này')
