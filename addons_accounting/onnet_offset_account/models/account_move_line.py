from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    offset_account_ids = fields.Many2many('account.account',
                                          compute='_compute_offset_account',
                                          readonly=False,
                                          )

    @api.depends('move_id.line_ids', 'move_id')
    def _compute_offset_account(self):
        for line in self:
            type_1 = ['product', 'tax', 'payment_term']
            type_2 = ['cogs']
            if line.display_type in type_1:
                offset_lines = line.move_id.line_ids.filtered(lambda x:
                                                              abs(x.balance * line.balance) != x.balance * line.balance
                                                              and x.display_type in type_1
                                                              )
                offset_accounts = offset_lines.mapped('account_id').ids
                line.offset_account_ids = offset_accounts
            elif line.display_type in type_2:
                offset_lines = line.move_id.line_ids.filtered(lambda x:
                                                              abs(x.balance * line.balance) != x.balance * line.balance
                                                              and x.display_type in type_2
                                                              )
                offset_accounts = offset_lines.mapped('account_id').ids
                line.offset_account_ids = offset_accounts
            else:
                line.offset_account_ids = False



