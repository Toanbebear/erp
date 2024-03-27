from odoo import fields, api, models, _
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
import datetime
from datetime import timedelta
import logging
import json


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for rec in self.filtered(lambda m: m.state == 'posted' and m.invoice_origin):
            sale_order = self.env['sale.order'].sudo().search([('name', 'like', rec.invoice_origin)], limit=1)
            if sale_order and self.env.company in sale_order.booking_id.company2_id and self.env.company != sale_order.booking_id.company_id:
                rec.create_account_move(sale_order, rec)
        return res

    def get_rate(self, company_a, company_b):
        rate = 0
        for line in company_a.service_allocation_rate_id.line_ids:
            if line.introduced_company == company_b:
                rate = line.rate
        return rate

    def create_account_move(self, sale_order, account_move):
        Move_Obj = self.env['account.move'].sudo()
        SalePayment_Obj = self.env['crm.sale.payment'].sudo()
        company_sci = self.env['res.company'].sudo().search([('x_is_corporation', '=', True)], limit=1)
        if not company_sci:
            raise UserError(
                'Không tìm thấy Tổng công ty. Vui lòng thiết lập Tổng công ty trước khi thao tác. Xin cảm ơn')
        company_b = self.env.company
        partner_b = company_b.partner_id
        company_a = sale_order.booking_id.company_id
        partner_a = company_a.partner_id
        payment_b_ids = self.env['account.payment'].search(
            [('crm_id', '=', sale_order.booking_id.id), ('company_id', '=', company_b.id)])
        partner_lead = sale_order.booking_id.partner_id
        # Tổng tiền trên hóa đơn của cty B
        amount_total = account_move.amount_total if account_move else 0
        # --- tổng số tiền được phân bổ cho công ty B ----
        # (nguồn từ các thanh toán gắn với booking)
        amount_recei_b = sum(
            payment_b_ids.service_ids.filtered(lambda s: s.company_id == company_b).mapped('prepayment_amount'))
        # (nguồn từ các điều chuyển gắn với booking)
        amount_sale_payment_b = sum(SalePayment_Obj.search(
            [('company_id', '=', company_b.id), ('booking_id', '=', sale_order.booking_id.id),
             ('transfer_payment_id', '!=', False)]).mapped('amount_proceeds'))
        # --- số tiền trong bút toán xử lý thu/chi hộ -----
        amount_help = amount_total - amount_recei_b - amount_sale_payment_b
        # --- số tiền trong bút toán xử lý tỷ lệ phân bổ
        # (nguồn từ các thanh toán gắn với booking)
        amount_recei_a = sum(
            payment_b_ids.service_ids.filtered(lambda s: s.company_id == company_a).mapped('prepayment_amount'))
        # (nguồn từ các điều chuyển gắn với booking)
        amount_sale_payment_a = sum(SalePayment_Obj.search(
            [('company_id', '=', company_a.id), ('booking_id', '=', sale_order.booking_id.id),
             ('transfer_payment_id', '!=', False)]).mapped('amount_proceeds'))
        revenue_a_return = amount_recei_a + amount_sale_payment_a
        if amount_help == 0 or revenue_a_return == 0:
            return True
        # -------------------------------------------

        # ---------- Công ty B -------------
        acc_receivable_b = partner_lead.with_context(force_company=company_b.id).property_account_receivable_id
        if not acc_receivable_b:
            raise UserError(
                'Không tìm thấy Tài khoản Phải thu của khách hàng %s ở cty %s' % (partner_lead.name, company_b.name))
        acc_receivable_setting_b = company_b.internal_transfer_account
        if not acc_receivable_setting_b:
            raise UserError(
                'Không tìm thấy Tài khoản Phải thu được thiết lập ở cty %s' % (company_b.name))
        acc_payable_setting_b = company_b.x_internal_payable_account_id
        if not acc_payable_setting_b:
            raise UserError(
                'Tài khoản phải trả nội bộ chưa được thiết lập ở công ty %s' % (company_b.name))

        # todo tạo bút toán ty B
        ref = 'Xử lý tỷ lệ phân bổ'
        if revenue_a_return >= 0:
            partner_credit = partner_a
            partner_debit = partner_lead
            account_credit_id = acc_payable_setting_b
            account_id_debit = acc_receivable_b
            amount = revenue_a_return
        else:
            partner_credit = partner_lead
            partner_debit = partner_a
            account_credit_id = acc_receivable_b
            account_id_debit = acc_payable_setting_b
            amount = -revenue_a_return
        move_argvs = []
        move_argvs = self.get_account_move_vals(account_credit_id, account_id_debit,
                                                company_b,
                                                partner_credit, partner_debit, ref, amount)
        move_argvs['partner_id'] = partner_lead.id
        move_b1 = Move_Obj.create(move_argvs)
        move_b1.post()

        account_credit_id = acc_receivable_b
        account_id_debit = acc_receivable_setting_b
        partner_credit = partner_lead
        partner_debit = partner_a
        ref = 'Xử lý thu hộ/ chi hộ'
        amount = amount_help
        move_argvs = []
        move_argvs = self.get_account_move_vals(account_credit_id, account_id_debit,
                                                company_b, partner_credit, partner_debit,
                                                ref, amount)
        move_argvs['partner_id'] = partner_lead.id
        move_b2 = Move_Obj.create(move_argvs)
        move_b2.post()
        # ---------- Công ty A -------------
        acc_receivable_a = partner_lead.with_context(force_company=company_a.id).property_account_receivable_id
        if not acc_receivable_a:
            raise UserError(
                'Không tìm thấy Tài khoản Phải thu của khách hàng %s ở cty %s' % (partner_lead.name, company_a.name))
        acc_receivable_setting_a = company_a.internal_transfer_account
        if not acc_receivable_setting_a:
            raise UserError(
                'Không tìm thấy Tài khoản Phải thu được thiết lập ở cty %s' % (company_a.name))
        acc_payable_setting_a = company_a.x_internal_payable_account_id
        if not acc_payable_setting_a:
            raise UserError(
                'Tài khoản phải trả nội bộ chưa được thiết lập ở công ty %s' % (company_a.name))

        # todo tạo bút toán cty A
        ref = 'Xử lý tỷ lệ phân bổ'
        if revenue_a_return >= 0:
            partner_credit = partner_lead
            partner_debit = partner_b.sudo()
            account_credit_id = acc_receivable_a
            account_id_debit = acc_receivable_setting_a
            amount = revenue_a_return
        else:
            partner_credit = partner_b.sudo()
            partner_debit = partner_lead
            account_credit_id = acc_receivable_setting_a
            account_id_debit = acc_receivable_a
            amount = -revenue_a_return
        move_argvs = []
        move_argvs = self.get_account_move_vals(account_credit_id, account_id_debit,
                                                company_a, partner_credit, partner_debit, ref, amount)
        move_a1 = Move_Obj.create(move_argvs)
        move_a1.company_id = company_a.id
        move_a1.partner_id = partner_lead.id
        move_a1.post()
        # tạo thêm bút toán cho cty A
        account_credit_id = acc_payable_setting_a
        account_id_debit = acc_receivable_a
        partner_credit = partner_b
        partner_debit = partner_lead
        ref = 'Xử lý thu hộ/ chi hộ'
        amount = amount_help
        move_argvs = []
        move_argvs = self.get_account_move_vals(account_credit_id, account_id_debit,
                                                company_a, partner_credit, partner_debit, ref, amount)
        move_a2 = Move_Obj.create(move_argvs)
        move_a2.company_id = company_a.id
        move_a2.partner_id = partner_lead.id
        move_a2.post()

        # todo tạo bút toán cty SCI
        acc_receivable_setting_sci = company_sci.internal_transfer_account
        if not acc_receivable_setting_sci:
            raise UserError(
                'Không tìm thấy Tài khoản Phải thu được thiết lập ở cty %s' % (company_sci.name))
        account_credit_id = acc_receivable_setting_sci
        account_id_debit = acc_receivable_setting_sci
        ref = 'Netoff ở SCI'
        if revenue_a_return >= 0:
            partner_credit = partner_b.sudo()
            partner_debit = partner_a.sudo()
            amount = revenue_a_return
        else:
            partner_credit = partner_a.sudo()
            partner_debit = partner_b.sudo()
            amount = -revenue_a_return
        move_argvs = []
        move_argvs = self.get_account_move_vals(account_credit_id, account_id_debit,
                                                company_sci, partner_credit, partner_debit, ref, amount)
        move_sci = Move_Obj.create(move_argvs)
        move_sci.company_id = company_sci.id
        move_sci.partner_id = partner_lead.id
        move_sci.post()

    def get_account_move_vals(self, account_credit_id, account_id_debit, company_id, partner_credit,
                              partner_debit, ref, amount):
        today = datetime.date.today()
        journal_id = company_id.sudo().journal_internal_intro_service_id
        if not journal_id:
            raise UserError('Không tìm thấy Sổ nhật ký giới thiệu dịch vụ của %s' % company_id.name)
        return {
            'ref': ref,
            'journal_id': journal_id.id,
            'date': today,
            'type': 'entry',
            'invoice_date': today,
            'invoice_date_due': today,
            'company_id': company_id.id,
            'currency_id': self.currency_id.id,
            'line_ids': [
                (0, 0, self.get_account_move_line_vals(partner_id=partner_credit.id,
                                                       account_id=account_credit_id.id,
                                                       company_id=company_id.id,
                                                       credit=amount)),
                (0, 0, self.get_account_move_line_vals(partner_id=partner_debit.id,
                                                       account_id=account_id_debit.id,
                                                       company_id=company_id.id,
                                                       debit=amount))
            ]
        }

    def get_account_move_line_vals(self, partner_id, account_id, company_id, credit=0, debit=0, name=''):
        return {
            'partner_id': partner_id,
            'account_id': account_id,
            'credit': abs(credit),
            'debit': abs(debit),
            'name': name,
            'company_id': company_id,
        }
