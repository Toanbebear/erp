from odoo import fields, models, api


class CollaboratorAccount(models.Model):
    _name = 'collaborator.account'
    _description = 'Tài khoản'

    collaborator_id = fields.Many2one('collaborator.collaborator', string='Cộng tác viên')
    contract_id = fields.Many2one('collaborator.contract', string='Hợp đồng')
    company_id = fields.Many2one('res.company', string='Công ty')

    amount_total = fields.Monetary('Tổng tiền')
    amount_used = fields.Monetary('Tổng tiền đã chi')
    amount_remain = fields.Monetary('Tổng tiền còn lại', compute='set_amount_remain')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)

    @api.depends('amount_remain', 'amount_total')
    def set_amount_remain(self):
        for rec in self:
            # Tổng tiền còn lại = tổng tiền ban đầu - tổng tiền đã chi
            rec.amount_remain = rec.amount_total - rec.amount_used
