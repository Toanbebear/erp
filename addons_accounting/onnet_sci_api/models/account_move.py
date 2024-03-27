from odoo import api, fields, models, _, tools

class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_user_entry_id = fields.Many2one('res.users', copy=False, tracking=True,
        string='Salesperson',
        default=lambda self: self.env.user)