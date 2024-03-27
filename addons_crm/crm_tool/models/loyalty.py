from odoo import models


class LoyaltyUpdateLoyalty(models.Model):
    _inherit = "crm.loyalty.card"

    def update_loyalty(self):
        return {
            'name': 'Cập nhật thẻ thành viên',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_tool.view_form_update_loyalty').id,
            'res_model': 'update.loyalty',
            'context': {
                'default_loyalty': self.id,
                'default_date_interaction': self.date_interaction,
                'default_amount': self.amount,
            },
            'target': 'new',
        }
