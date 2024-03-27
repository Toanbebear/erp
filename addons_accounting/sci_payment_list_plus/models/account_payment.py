from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, Warning


class AccountPaymentListInherit(models.Model):
    _inherit = 'payment.list'

    ref_payment_id = fields.Char(string='Payment ID')

    @api.model
    def create(self, vals):
        rec = super(AccountPaymentListInherit, self).create(vals)
        if rec.ref_payment_id:
            origin_payment = self.env['account.payment'].browse(int(rec.ref_payment_id))
            origin_payment.flag_list = False
            for pay in rec.payment_ids:
                pay.flag_list = False
        return rec


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    flag_list = fields.Boolean(string='Cho phép lập bảng kê', default=True)

    def create_payment_list_from_payment(self):
        return {
            'name': _('Bảng kê thanh toán'),
            'type': 'ir.actions.act_window',
            'res_model': 'payment.list',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_ref_payment_id': self.id,
                'default_payment_type': self.payment_type,
                'default_payment_date': self.payment_date,
                'default_crm_id': self.crm_id.id,
                'default_communication': self.communication,
                'default_partner_type': self.partner_type,
                'default_partner_id': self.partner_id.id,
                'default_company_id': self.company_id.id,
            }
        }

    @api.model
    def create(self, vals):
        if vals.get('payment_ids', False):
            vals['flag_list'] = False
        return super(AccountPaymentInherit, self).create(vals)

    def post(self):
        super(AccountPaymentInherit, self).post()
        payment_list = self.payment_list_id
        if payment_list.ref_payment_id and payment_list.state == 'done':
            payment = self.env['account.payment'].search([('id', '=', payment_list.ref_payment_id)])
            if payment:
                if payment.state == 'draft':
                    payment.sudo().unlink()
                else:
                    raise UserError(_('Phiếu yêu cầu thu phí không thể xóa do có trạng thái %s.') % payment.state)
            else:
                raise Warning(_('Phiếu yêu cầu thu phí ID: %s không còn tồn tại') % payment_list.ref_payment_id)

    def button_payment_list_entries(self):
        return {
            'name': _('Bảng kê thanh toán'),
            'view_mode': 'tree,form',
            'res_model': 'payment.list',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('ref_payment_id', '=', self.id)],
        }

    @api.onchange('payment_method', 'company_id')
    def domain_journal_by_payment_method(self):
        method = ''
        if self.payment_method and self.company_id:
            if self.payment_method == 'tm':
                method = 'cash'
            elif self.payment_method in ['ck', 'pos', 'cdt']:
                method = 'bank'
            return {'domain': {'journal_id': [
                ('id', 'in', self.env['account.journal'].search(
                    [('company_id', '=', self.company_id.id), ('type', '=', method)]).ids)]}}
