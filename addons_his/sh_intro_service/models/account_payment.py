from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    internal_payment_type = fields.Selection([('tai_don_vi', _('Tại đơn vị')), ('thu_ho', _('Thu hộ')), ('chi_ho', _('Chi hộ'))], string=_('Loại giao dịch nội bộ'), default='tai_don_vi')

    def get_rate(self, company_a, company_b):
        rate = 0
        for line in company_a.service_allocation_rate_id.line_ids:
            if line.introduced_company == company_b:
                rate = line.rate
        return rate

    @api.model
    def create(self, values):
        Obj_detail_payment = self.env['crm.account.payment.detail']
        res = super(AccountPayment, self).create(values)
        if res.service_ids and res.crm_id.company2_id:
            service_ids = res.service_ids
            for service_payment in service_ids:
                rate_company_share = 0
                # them detail payment theo số lượng cty được share trong crm_lead
                if self.env.company != res.crm_id.company_id and self.env.company.id in res.crm_id.company2_id.ids:
                    rate = self.get_rate(res.crm_id.company_id, self.env.company)
                    detail_new = Obj_detail_payment.sudo().create({
                        'account_payment_id': res.id,
                        'crm_line_id': service_payment.crm_line_id.id,
                        'allocation_rate': rate,
                        'allocation_amount': service_payment.crm_line_id.total * int(rate) / 100
                    })
                    # trường company_id bên tasys khai báo là trường related
                    detail_new.company_id = self.env.company.id
                    rate_company_share += rate
                service_payment.write({
                    'allocation_rate': 100 - rate_company_share,
                    'allocation_amount': service_payment.crm_line_id.total * int(100 - int(rate_company_share)) / 100
                })
        return res

    @api.constrains('service_ids')
    def constrain_service_ids(self):
        for payment in self.filtered(lambda p:p.service_ids):
            for crm_line in payment.service_ids.mapped('crm_line_id'):
                if sum(payment.service_ids.filtered(lambda s:s.crm_line_id == crm_line).mapped('allocation_rate')) > 100:
                    raise UserError("Tỷ lệ phân bổ dịch vụ tại công ty {0} vượt quá 100%. Vui lòng kiểm tra lại".format(self.env.company.name))


    def _prepare_payment_moves(self):
        res = super(AccountPayment, self)._prepare_payment_moves()
        for transfer_move_vals in res:
            if transfer_move_vals['journal_id']:
                journal = self.env['account.journal'].sudo().browse(transfer_move_vals['journal_id'])
                if journal.read():
                    if journal.shared_bank_account:
                        for line in transfer_move_vals['line_ids']:
                            if line[2]['debit'] > 0:
                                line[2]['partner_id'] = journal.shared_company_id.sudo().partner_id.id
        return res

    def post(self):
        res = super(AccountPayment, self).post()
        if res:
            for rec in self:

                if rec.state == 'posted' and rec.journal_id.shared_bank_account:
                    data = rec._prepare_payment_moves()
                    shared_journal = rec.journal_id.shared_journal_id.sudo()
                    shared_company = rec.journal_id.shared_company_id.sudo()

                    for item in data:
                        item['journal_id'] = shared_journal.id
                        item['company_id'] = shared_company.id
                        item['ref'] = item['name']
                        item['name'] = '/'
                        for line in item['line_ids']:
                            line[2]['name'] = False
                            line[2]['payment_id'] = False
                            if line[2]['debit'] > 0:
                                line[2]['account_id'] = shared_journal.sudo().default_debit_account_id.id
                                line[2]['partner_id'] = shared_company.partner_id.id
                            elif line[2]['credit'] > 0:
                                line[2]['account_id'] = shared_company.x_internal_payable_account_id.id
                                line[2]['partner_id'] = rec.company_id.partner_id.id
                    AccountMove = self.env['account.move'].sudo().create(data)
        return res

    @api.onchange('payment_type')
    def _change_payment_type(self):
        if self.payment_type == 'transfer':
            self.internal_payment_type = 'tai_don_vi'
        elif self.payment_type == 'inbound':
            if self.internal_payment_type == 'chi_ho':
                self.internal_payment_type = 'thu_ho'
        elif self.payment_type == 'outbound':
            if self.internal_payment_type == 'thu_ho':
                self.internal_payment_type = 'chi_ho'

    @api.onchange('internal_payment_type')
    def _change_internal_payment_type(self):
        if self.internal_payment_type == 'thu_ho':
            self.payment_type = 'inbound'
        elif self.internal_payment_type == 'chi_ho':
            self.payment_type = 'outbound'