# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from random import randint
import re


# def num2words_vnm(num):
#     under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
#                 'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
#     tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
#     above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}
#
#     if num < 20:
#         return under_20[num]
#
#     elif num < 100:
#         under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
#         result = tens[num // 10 - 2]
#         if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
#             result += ' ' + under_20[num % 10]
#         return result
#
#     else:
#         unit = max([key for key in above_100.keys() if key <= num])
#         result = num2words_vnm(num // unit) + ' ' + above_100[unit]
#         if num % unit != 0:
#             if num > 1000 and num % unit < unit / 10:
#                 result += ' không trăm'
#             if 1 < num % unit < 10:
#                 result += ' linh'
#             result += ' ' + num2words_vnm(num % unit)
#     return result.capitalize()


class SCIAccountPayment(models.Model):
    _inherit = 'account.payment'

    company2_id = fields.Many2one('res.company', string="Nơi làm dịch vụ")
    # Trường hợp tạo phiếu điều chỉnh, phải chỉ ra điều chỉnh cho phiếu account.payment nào.
    entry_payment_id = fields.Many2one('account.payment', string='Phiếu ban đầu')

    payment_ids = fields.One2many('account.payment', 'entry_payment_id', string='Phiếu con')

    amount_total = fields.Monetary(string='Tổng tiền ban đầu', related='crm_id.amount_total')
    amount_paid = fields.Monetary(string='Tổng tiền khách đã trả', related='crm_id.amount_paid')
    amount_used = fields.Monetary(string='Tổng tiền khách sử dụng', related='crm_id.amount_used')
    amount_remain = fields.Monetary(string='Tổng tiền còn lại', related='crm_id.amount_remain')
    is_child = fields.Boolean(string='Là phiếu điều chỉnh', default=False)
    is_payment_for_share = fields.Boolean(string='Phiếu thanh toán là thu chị hộ', compute='_get_is_payment', store=True)
    behalf_id = fields.Many2one('account.register.payment.behalf')

    @api.depends('company2_id')
    def _get_is_payment(self):
        for rec in self:
            if rec.company2_id:
                rec.is_payment_for_share = True
            else:
                rec.is_payment_for_share = False

    @api.onchange('walkin')
    def _get_amount_by_walkin(self):
        for rec in self.sudo():
            rec.amount = rec.walkin.sale_order_id.amount_total - rec.walkin.sale_order_id.amount_remain

    @api.onchange('walkin')
    def _get_patient(self):
        if self.walkin:
            self.patient = self.walkin.patient.id

    @api.onchange('crm_id')
    def _get_company_by_crm_id(self):
        if self.crm_id:
            self.company2_id = self.crm_id.company_id

    @api.onchange('partner_id', 'company2_id','walkin')
    def _get_communication(self):
        if self.payment_type == 'inbound' and self.company2_id:
            self.communication = 'Thu hộ %s cho %s %s' % (self.crm_id.company_id.name, self.crm_id.name, self.walkin.name and '| ' + self.walkin.name or '')
        elif self.payment_type == 'outbound' and self.company2_id:
            self.communication = 'Chi hộ %s %s' % (self.crm_id.company_id.name, self.walkin.name)

    @api.onchange('amount')
    # Tổng số tiền các lần điều chỉnh giảm không được vượt quá số tiền ban đầu.
    def _validate_amount(self):
        self.ensure_one()
        if self.entry_payment_id:
            # Số tiền của phiếu gốc ban đầu
            amount = self.entry_payment_id.amount

            # Tính tổng các phiếu điều chỉnh đã có:
            amount_adjusted = sum([element.amount for element in self.entry_payment_id.payment_ids])

            if self.amount + amount_adjusted > amount:
                raise UserError(_("Tổng số tiền điều chỉnh tại các phiếu điều chỉnh giảm, vượt quá số thu ban đầu."))

    def _check_payment(self):
        result = False
        # Đưa ra cảnh báo nếu số tiền  khách đóng chưa đủ so với tiền trên phiếu khám.
        for rec in self:
            if rec.payment_type != 'outbound':  # nếu hóa đơn hoàn tiền cho khách
                total_so = rec.walkin.sale_order_id.amount_total  # Tổng tiền trên booking
                # amount_set = rec.walkin.sale_order_id.set_total  # Số tiền khách đã sử dụng
                total_so_remain = rec.walkin.sale_order_id.amount_remain  # Số tiền còn lại
                amount_owed = rec.walkin.sale_order_id.amount_owed  # Số tiền khách được duyệt nợ

                # Trường hợp có phiếu khám
                if rec.walkin and rec.walkin.state not in ['Completed', 'Cancelled']:
                    # order duyệt nợ -> đi thẳng
                    if rec.walkin.sale_order_id.debt_review_id and total_so <= (total_so_remain + amount_owed):
                        result = True

                    # order nha khoa,amount_set > 0 and remain > amount_set
                    elif rec.walkin.sale_order_id.odontology is True and total_so_remain >= amount_owed:
                        result = True

                    # order nha khoa, amount_set > 0 , set > remain
                    elif rec.walkin.sale_order_id.odontology is True and total_so > total_so_remain:
                        result = False

                    elif total_so_remain >= total_so:
                        result = True

                    elif total_so > total_so_remain:  # thiếu tiền
                        result = False

                    else:
                        result = True
                # Trường hợp không có phiếu khám
                else:
                    result = False

        return result

    def internal_debt(self):
        # TODO sinh ra phiếu ghi nhận công nộ phải thu tại A, và công nợ phải trả tại B
        self.env['ir.actions.actions'].clear_caches()

        # Đảm bảo các phiếu điều chỉnh phải được xác nhận hết trước khi gửi đối chiếu công nợ
        check = True
        if self.payment_ids:
            check = all([rec.state in ('posted', 'cancelled') for rec in self.payment_ids])

        if not check:
            raise UserError(_("Có phiếu điều chỉnh chưa được xác nhận"))

        '''
            Kiểm tra account.payment có phiếu điều chỉnh chưa được xác nhận không.
            Kiểm tra số tiền gửi xác nhận có khớp với số tiền phải thu không.
                Nếu khớp cho pass phiếu khám và gửi xác nhận
                Nếu không khớp không pass phiếu khám và không gửi xác nhận
        '''
        # Tìm trong account.payment tất cả các phiếu thanh toán thanh toán cho phiếu khám. Được tạp bởi bên thu hộ.
        payments = self.env['account.payment'].search(
            [('walkin', '=', self.walkin.id), ('company_id', '=', self.company_id.id), ('payment_type', '=', 'inbound')])

        amount_result = 0.0
        string = ''
        count = 0
        for pay in payments:
            if pay.state == 'posted':
                # Số tiền gốc của phiếu.
                amount = pay.amount
                # Số tiền điều chỉnh giảm của phiếu
                amount_adjusted = sum([element.amount for element in pay.payment_ids if element.payment_type == 'outbound'])
                amount_result += amount - amount_adjusted
            elif pay.state != 'cancelled':
                string += ''.join(('|Phiếu thu: %s trạng thái: %s|' % (pay['name'], pay['state'])) + '\n')
                count += 1

        if count >= 1:
            raise UserError(_("Có phiếu thu chưa được xác nhận hết\n") + string)

        # TODO kiểm tra số tiền thu được của khách có khớp với số phải thu trên phiếu khám trên Booking không.
        # if self.amount > 0:
        # amount_adjusted = sum([element.amount for element in self.payment_ids if element.state == 'posted' and element.payment_type == 'outbound'])
        #
        # amount_inbound = sum([element.amount for element in self.payment_ids if element.state == 'posted' and element.payment_type == 'inbound'])
        #
        # result_amount = self.amount - amount_adjusted + amount_inbound

        if self.sudo()._check_payment():

            self.sudo().walkin.set_to_progress()

            string = 'Chi nhánh %s ghi nhận phải trả chi nhánh %s số tiền là %s' % (
                self.company_id.name, self.company2_id.name, (self.num2words_vnm(round(amount_result)) + ' đồng').lower())

            journal_id = self.env['account.journal'].search([('code', '=', 'PTRNB'), ('company_id', '=', self.company_id.id)]).id or ''

            vals = {
                'name': _('Xác nhận công nợ nội bộ'),  # label
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('sci_accounting.account_internal_debt_from').id,
                'res_model': 'account.internal.debt',  # model want to display
                'target': 'new',  # if you want popup
                'context': {
                    'default_payment_id': self.id,
                    'default_company_id': self.company_id.id,
                    'default_company2_id': self.company2_id.id,
                    'default_journal_id': journal_id,
                    'default_amount': float(amount_result),
                    'default_communication': string,
                }
            }
            return vals
        else:
            context = dict(self._context or {})
            if (self.walkin.sale_order_id.amount_total - self.walkin.sale_order_id.amount_remain != 0):
                context[
                    'message'] = 'Tổng số tiền thanh toán vẫn chưa đủ để thực hiện dịch vụ! Hãy thay toán thêm: %s VNĐ' % "{:,.0f}".format(
                    self.walkin.sale_order_id.amount_total - self.walkin.sale_order_id.amount_remain)
            else:
                context[
                    'message'] = 'Bạn chưa có phiếu khám, hãy tạo và chỉ định phiếu khám cho Booking: %s' % self.crm_id.name

            return {
                'name': _('Thông báo'),  # label
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref('sh_message.sh_message_wizard').id,
                'res_model': 'sh.message.wizard',  # model want to display
                'target': 'new',  # if you want popup
                'context': context,
            }

    def post(self):
        res = super(SCIAccountPayment, self).post()
        for rec in self.sudo():
            if rec.partner_type == 'customer' and rec.payment_type == 'outbound' and not rec.company2_id:
                partner_company = self.env['res.company'].search([('partner_id', '=', rec.partner_id.id)], limit=1)
                if partner_company:
                    journal = self.env['account.journal'].search(
                        [('type', '=', 'general'), ('company_id', '=', partner_company.id)], limit=1)
                    account = rec.company_id.partner_id.with_context(
                        force_company=partner_company.id).property_account_payable_id
                    acc_move_vals = {'date': rec.payment_date,
                                     'ref': rec.name,
                                     'journal_id': journal.id,
                                     'line_ids': [(0, 0, {'account_id': account.id,
                                                          'partner_id': rec.company_id.partner_id.id,
                                                          'name': rec.communication, 'credit': rec.amount}),
                                                  (0, 0, {'account_id': account.id, 'debit': rec.amount})]}
                    self.env['account.move'].create(acc_move_vals)
        return res

    def account_entries(self):
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:
            if rec.partner_type in ('customer', 'supplier') and rec.company_id != rec.company2_id:
                # Xác định giao dịch nội bộ: Loại đối tác là khách hàng, loại thanh toán là thu tiền, công ty company_id != company_id_2

                account = rec.journal_id
                company_id_partner = self.env['res.partner'].search([('id', '=', rec.company2_id.partner_id.id)], limit=1)

                if not rec.name:
                    rec.name = rec._get_rec_name()

                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company."))
                """
                [{
                'date': datetime.date(2021, 9, 27), 'ref': 'test 10', 'journal_id': 70, 'currency_id': 23, 'partner_id': 410754,'line_ids': 
                    [(0, 0, {'name': 'Khoản thanh toán của khách hàng', 'amount_currency': 0.0, 
                            'currency_id': False, 'debit': 0.0, 'credit': 123321.0, 'date_maturity': datetime.date(2021, 9, 27), 
                            'partner_id': 410754, 'account_id': 815, 'payment_id': 114638}), 
                    (0, 0, {'name': 'CUST.IN/2021/1469', 'amount_currency': -0.0, 
                            'currency_id': False, 'debit': 123321.0, 'credit': 0.0, 'date_maturity': datetime.date(2021, 9, 27),
                            'partner_id': 410754,'account_id': 1096,'payment_id': 114638})]
                }]
                """
                line_vals = super(SCIAccountPayment, self)._prepare_payment_moves()

                if rec.payment_type == 'inbound':
                    # TK Co
                    line_vals[0]['line_ids'][0][2]['account_id'] = company_id_partner.property_account_payable_id.id
                    line_vals[0]['line_ids'][0][2]['partner_id'] = company_id_partner.id
                    # TK No
                    line_vals[0]['line_ids'][1][2]['account_id'] = account.default_debit_account_id.id

                elif rec.payment_type == 'outbound':
                    if rec.is_child:
                        # TK Co
                        line_vals[0]['line_ids'][0][2]['account_id'] = company_id_partner.property_account_payable_id.id
                        line_vals[0]['line_ids'][0][2]['partner_id'] = company_id_partner.id
                        # TK No
                        line_vals[0]['line_ids'][1][2]['account_id'] = account.default_debit_account_id.id
                    else:
                        # TK No
                        line_vals[0]['line_ids'][0][2][
                            'account_id'] = company_id_partner.property_account_receivable_id.id
                        # TK Co
                        line_vals[0]['line_ids'][1][2]['account_id'] = account.default_debit_account_id.id

                        line_vals[0]['line_ids'][0][2]['partner_id'] = company_id_partner.id
                        line_vals[0]['line_ids'][1][2]['partner_id'] = rec.partner_id.id

                # Tạo bản ghi account.move
                moves = AccountMove.create(line_vals)
                moves.post()

                # Chuyển trạng thái của bản ghi account.payment thành xác nhận và đặt tên.
                move_name = rec._get_move_name_transfer_separator().join(moves.mapped('name'))
                rec.write({'state': 'posted', 'move_name': move_name})
                # TODO
                # Mỗi phiếu account.payment được xác nhận --> sinh ra phiếu account.move hạch toán ghi nhận phải thu phải trả hai công cty.
                # Lưu ý account.payment được sinh ra từ đề xuất thanh toán, sẽ không cho sửa số tiền khi đã sinh ra phiếu payment.
                if rec.behalf_id:
                    behalf = rec.sudo().behalf_id
                    behalf_parent = behalf.original_record
                    amount = rec.amount
                    # Nếu phiếu thanh toán đưa về dạng nháp thì không cho phép tạo mới bản ghi xác nhận công nợ nội bộ.
                    if not rec.check_account_move_behalf(behalf):
                        company_acc_move_vals = {'patient': '',
                                                 'date': rec.payment_date,
                                                 'ref': behalf.name,
                                                 'journal_id': behalf.journal_id.id,
                                                 'company_id': behalf.company_id.id,
                                                 'company2_id': behalf_parent.company_id.id,
                                                 'behalf_id': behalf.id,
                                                 'line_ids': [(0, 0, {'account_id': behalf.journal_id.default_debit_account_id.id,
                                                                      # Tài khoản ghi nợ
                                                                      'partner_id': behalf_parent.company_id.partner_id.id,  # Đối tượng
                                                                      'name': behalf.communication,
                                                                      'debit': amount,
                                                                      'credit': 0.0,
                                                                      'is_sci_lock': True}),
                                                              (0, 0, {'account_id': behalf.company_id.partner_id.property_account_receivable_id.id,
                                                                      # Tài khoản ghi có
                                                                      'partner_id': behalf_parent.company_id.partner_id.id,  # Đối tượng
                                                                      'name': behalf.communication,
                                                                      'debit': 0.0,
                                                                      'credit': amount,
                                                                      'is_sci_lock': False})
                                                              ]}

                        AccountMove.create(company_acc_move_vals).action_post()

                    if not rec.check_account_move_behalf(behalf_parent):
                        company_2_acc_move_vals = {'patient': '',
                                                   'date': rec.payment_date,
                                                   'ref': behalf.name,
                                                   'journal_id': behalf_parent.sudo().journal_id.id,
                                                   'company_id': rec.company2_id.id,
                                                   'company2_id': behalf.company_id.id,
                                                   'behalf_id': behalf_parent.id,
                                                   'line_ids': [(0, 0, {'account_id': rec.with_context(force_company=rec.company2_id.id).partner_id.property_account_payable_id.id,
                                                                        # Tài khoản ghi nợ
                                                                        'partner_id': rec.partner_id.id,  # Đối tượng
                                                                        'name': behalf.communication,
                                                                        'debit': amount,
                                                                        'credit': 0.0,
                                                                        'is_sci_lock': False}),
                                                                (0, 0, {'account_id': behalf_parent.sudo().journal_id.default_credit_account_id.id,  # Tài khoản ghi có
                                                                        'partner_id': behalf.company_id.partner_id.id,  # Đối tượng
                                                                        'name': behalf.communication,
                                                                        'debit': 0.0,
                                                                        'credit': amount,
                                                                        'is_sci_lock': True})
                                                                ]}

                        AccountMove.sudo().create(company_2_acc_move_vals).action_post()

                    # Các payment được sinh ra từ phiếu duyệt chi:
                    payments = self.env['account.payment'].search([('behalf_id', '=', behalf.id)])
                    if all(pay.state in ('posted', 'cancel') for pay in payments):
                        behalf.write({'state': 'posted'})
                        behalf_parent.write({'state': 'posted'})
                        i = 0
                        data = [element.amount_approval for element in behalf.behalf_lines]
                        for line in behalf_parent.behalf_lines:
                            line.amount_approval = data[i]
                            i += 1

        return True

    def _get_rec_name(self):
        self.ensure_one()

        if self.state != 'draft':
            raise UserError(_("Only a draft payment can be posted."))

        if any(inv.state != 'posted' for inv in self.invoice_ids):
            raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

        # keep the name in case of a payment reset to draft
        if not self.name:
            # Use the right sequence to set the name
            if self.payment_type == 'transfer':
                sequence_code = 'account.payment.transfer'
            else:
                if self.partner_type == 'customer':
                    if self.payment_type == 'inbound':
                        sequence_code = 'account.payment.customer.invoice'
                    if self.payment_type == 'outbound':
                        sequence_code = 'account.payment.customer.refund'
                if self.partner_type == 'supplier':
                    if self.payment_type == 'inbound':
                        sequence_code = 'account.payment.supplier.refund'
                    if self.payment_type == 'outbound':
                        sequence_code = 'account.payment.supplier.invoice'
            return self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=self.payment_date)

    def adjustment_journal_entry(self):
        self.ensure_one()
        view_id = self.env.ref('sci_accounting.view_account_payment_transfer_adjustment_form').id
        string = "Đ/C giảm cho phiếu thu số: %s" % self.name

        return {'type': 'ir.actions.act_window',
                'name': _('Materials of Walkin Details'),
                'res_model': 'account.payment',
                'target': 'new',
                'view_mode': 'form',
                'context': {
                    'default_is_child': True,
                    'default_entry_payment_id': self.id,
                    'default_payment_type': 'outbound',
                    'default_payment_method': self.payment_method,
                    'default_journal_id': self.journal_id.id,
                    'default_partner_id': self.partner_id.id,
                    'default_company_id_2': self.company2_id.id,
                    'default_crm_id': self.crm_id.id,
                    'default_walkin': self.walkin.id,
                    'default_partner_type': self.partner_type,
                    'default_communication': string,
                },
                'views': [[view_id, 'form']],
                }

    def check_account_move_behalf(self, behalf_id):
        account_move = self.env['account.move'].search([('behalf_id', 'in', behalf_id.ids)])
        if account_move:
            return True
        else:
            return False
