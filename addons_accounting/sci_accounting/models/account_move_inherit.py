from odoo import fields, models, api
from odoo.exceptions import ValidationError


class SCIAccountMoveInherit(models.Model):
    _inherit = 'account.move'
    _description = 'Description'

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('sent', 'Đã gửi'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    company2_id = fields.Many2one('res.company', string='CN chi hộ')
    behalf_id = fields.Many2one('account.register.payment.behalf')

    def action_post(self):
        # validate Bút toán của cty nào thì người dùng đứng ở cty đó được vào sổ
        selected_company = self.env.company
        for rec in self:
            if (rec.company_id != selected_company) and (self.env.user.id != 1):
                raise ValidationError("Bút toán của cty nào thì người dùng đứng ở cty đó được vào sổ.")

        res = super(SCIAccountMoveInherit, self).action_post()
        for rec in self:
            if rec.company2_id and rec.company_id:
                ref = rec.ref
                # Tìm trong account.move mã phiếu ref, với điều kiện trường company_id khác với company đang mở.
                account_move = self.env['account.move'].sudo().search([('ref', '=', ref), ('company_id', '!=', rec.company_id.id)])
                account_move.post()
                account_payment = self.env['account.payment'].sudo().search([('name', '=', ref), ('company_id', '!=', rec.company_id.id)])
                account_payment.write({'state': 'reconciled'})
        return res

    @api.constrains('ref')
    def _check_duplicate_supplier_reference(self):
        return