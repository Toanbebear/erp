from odoo import models


class InheritCrmLead(models.Model):
    _inherit = "crm.lead"

    def tao_so_am(self):
        return {
            'name': 'Tạo SO âm',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_tool.view_create_negative_so').id,
            'res_model': 'create.negative.so',
            'context': {
                'default_booking': self.id,
                'default_partner': self.partner_id.id,
            },
            'target': 'new',
        }

    def update_line_consultant(self):
        if self.env.company.brand_id.id == 3:
            line_ids = self.crm_line_ids.filtered(
                lambda l: (l.stage in ['new', 'processing']) and not l.crm_information_ids)
        else:
            line_ids = self.crm_line_ids.filtered(
                lambda l: (l.stage in ['new', 'processing']) and not l.consultants_1)
        return {
            'name': 'Cập nhật tư vấn viên hàng loạt',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_tool.view_form_update_line_consultants').id,
            'res_model': 'update.line.consultants',
            'context': {
                'default_booking': self.id,
                'default_line_ids': [(6, 0, line_ids.ids)],
            },
            'target': 'new',
        }
