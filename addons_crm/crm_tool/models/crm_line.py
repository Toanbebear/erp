from odoo import models


class InheritCrmLine(models.Model):
    _inherit = "crm.line"

    def update_unit_price(self):
        return {
            'name': 'CẬP NHẬT DÒNG DỊCH VỤ',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_tool.view_form_update_crm_line').id,
            'res_model': 'update.crm.line',
            'context': {
                'default_line': self.id
            },
            'target': 'new',
        }
