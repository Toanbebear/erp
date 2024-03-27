from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def change_journal(self):
        return {
            'name': 'Đổi sổ nhật ký',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_tool.view_form_change_journal').id,
            'res_model': 'change.journal',
            'context': {
                'default_move_id': self.id,
                'default_type': 'move',
            },
            'target': 'new',
        }
