from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def change_journal(self):
        return {
            'name': 'Đổi sổ nhật ký',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_tool.view_form_change_journal').id,
            'res_model': 'change.journal',
            'context': {
                'default_payment_id': self.id,
                'default_type': 'payment',
            },
            'target': 'new',
        }
