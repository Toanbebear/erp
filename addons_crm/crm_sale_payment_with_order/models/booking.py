from odoo import models, fields, api


class CRMLineDebt(models.Model):
    _inherit = 'crm.line'

    amount_owed = fields.Monetary('Tiền nợ')


class CRMLineProductDebt(models.Model):
    _inherit = 'crm.line.product'

    amount_owed = fields.Monetary('Tiền nợ')


class CRMButtonDebt(models.Model):
    _inherit = 'crm.lead'

    def request_debt_review(self):
        return {
            'name': 'Yêu cầu duyệt nợ',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('crm_base.debt_view_form').id,
            'res_model': 'crm.debt.review',
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_company_id': self.company_id.id,
                'default_booking_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }