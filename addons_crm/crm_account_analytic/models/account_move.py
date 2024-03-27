from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo import fields, models, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    cost_allocation_count = fields.Integer(string='PBCP', compute='compute_cost_allocation_count')
    cost_allocation_id = fields.Many2one('cost.allocation')

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', '/') == '/':
    #         vals['name'] = self.env['ir.sequence'].next_by_code(
    #             'account.move') or '/'
    #     result = super(AccountMove, self).create(vals)
    #     return result

    def compute_cost_allocation_count(self):
        for rec in self:
            rec.cost_allocation_count = rec.env['cost.allocation'].search_count(
                [('account_move_ids', '=', rec.id)])

    def cost_allocation(self):
        self.ensure_one()
        if self.state != 'posted':
            context = {
                'default_account_move_ids': [(4, self.id)],
                'create': False
            }
        else:
            journal_sci_id = self.env['account.journal.equivalent'].search([
                ('account_equivalent_ids', '=', self.journal_id.id),
            ], limit=1).account_sci_id
            account_debit_id = self.env['account.account.equivalent'].search([
                ('account_equivalent_ids', '=', self.line_ids[0].account_id.id),
            ], limit=1).account_sci_id
            account_credit_id = self.env['account.account.equivalent'].search([
                ('account_equivalent_ids', '=', self.line_ids[1].account_id.id),
            ], limit=1).account_sci_id
            analytic_group_id = self.env['account.analytic.group'].search([
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            move_lines = [
                (0, 0, {
                    'account_id': account_debit_id.id,
                    'debit': self.line_ids[0].debit,
                    'credit': self.line_ids[0].credit,
                }),
                (0, 0, {
                    'account_id': account_credit_id.id,
                    'debit': self.line_ids[1].debit,
                    'credit': self.line_ids[1].credit
                })
            ]
            context = {
                'default_account_move_ids': [(4, self.id)],
                'default_date': self.date,
                'default_account_journal_id': journal_sci_id.id,
                'default_account_move_allocation_line_ids': move_lines,
                'default_account_analytic_group_id': analytic_group_id.parent_id.id or analytic_group_id.id,
            }
        return {
            'name': _('Phân bổ chi phí'),
            'view_mode': 'tree,form',
            'res_model': 'cost.allocation',
            'type': 'ir.actions.act_window',
            'domain': [('account_move_ids', '=', self.id)],
            'context': context
        }
