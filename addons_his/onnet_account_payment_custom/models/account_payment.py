##############################################################################
#    Copyright (C) 2018 shealth (<http://scigroup.com.vn/>). All Rights Reserved
#    shealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, shealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
# Inherit Payment

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    internal_payment_type = fields.Selection([('tai_don_vi', _('Tại đơn vị')), ('thu_ho', _('Thu hộ')), ('chi_ho', _('Chị hộ'))], string=_('Loại giao dịch nội bộ'), default='tai_don_vi')
    x_receive_company_id = fields.Many2one('res.company', 'Công ty giao dịch')


    # XÁC NHẬN THANH TOÁN
    def post(self):
        Move_Obj = self.env['account.move'].sudo()
        for payment in self:
            rec = super(AccountPayment, self).post()
            # nghiệp vụ thu hộ
            if payment.x_receive_company_id:
                company_b = payment.x_receive_company_id
                company_a = self.env.company
                if company_b ==  company_a:
                    raise UserError("""Bạn đang làm nghiệp vụ thu hộ. Vui lòng chọn lại dòng "Thu hộ công ty" khác với công ty hiện tại (%s) """% company_a.name)
                company_sci = self.env['res.company'].sudo().search([('x_is_corporation', '=', True)], limit=1)
                if not company_sci:
                    raise UserError('Không tìm thấy Tổng công ty. Vui lòng thiết lập Tổng công ty trước khi thao tác. Xin cảm ơn')
                # acc_payable_a = company_a.currency_id.with_context(force_company=company_a.id).x_payable_account_id
                acc_payable_a = company_a.x_internal_payable_account_id
                if not acc_payable_a:
                    raise UserError('Không tìm thấy Tài khoản phải trả nội bộ của %s' % (company_a.name))
                acc_payable_b = company_b.x_internal_payable_account_id
                # acc_payable_b = company_a.currency_id.with_context(force_company=company_b.id).x_payable_account_id
                if not acc_payable_b:
                    raise UserError('Không tìm thấy Tài khoản phải trả nội bộ của %s' % (company_a.name))
                acc_payable_sci = company_sci.x_internal_payable_account_id
                if not acc_payable_sci:
                    raise UserError('Không tìm thấy Tài khoản phải trả nội bộ của %s' % (company_sci.name))
                if not payment.journal_id.default_debit_account_id:
                    raise UserError('Không tìm thấy Tài khoản ghi nợ mặc định của hình thức thanh toán %s' % (payment.journal_id.name))
                acc_receivable_b = payment.partner_id.with_context(force_company=company_b.id).property_account_receivable_id
                if not acc_receivable_b:
                    raise UserError('Không tìm thấy Tài khoản Phải thu của khách hàng %s' % payment.partner_id.name)
                if not company_a.internal_transfer_account:
                    raise UserError('Không tìm thấy Tài khoản Phải thu điều chuyển nội bộ của %s' % company_a.name)
                acc_internal_trasf_b = company_b.internal_transfer_account
                # acc_internal_trasf_b = company_b.currency_id.with_context(force_company=company_b.id).internal_transfer_account
                if not acc_internal_trasf_b:
                    raise UserError('Không tìm thấy Tài khoản Phải thu điều chuyển nội bộ của %s' % company_b.name)
                acc_internal_trasf_sci = company_sci.internal_transfer_account
                # acc_internal_trasf_sci = company_sci.currency_id.with_context(force_company=company_sci.id).internal_transfer_account
                if not acc_internal_trasf_sci:
                    raise UserError('Không tìm thấy Tài khoản Phải thu điều chuyển nội bộ của %s' % company_sci.name)
                journal_internal_collect_a = company_a.sudo().journal_internal_collect_id
                if not journal_internal_collect_a:
                    raise UserError('Không tìm thấy Sổ nhật ký thu hộ của %s' % company_a.name)
                journal_internal_collect_b = company_b.sudo().journal_internal_collect_id
                if not journal_internal_collect_b:
                    raise UserError('Không tìm thấy Sổ nhật ký thu hộ của %s' % company_b.name)
                journal_internal_collect_sci = company_sci.sudo().journal_internal_collect_id
                if not journal_internal_collect_sci:
                    raise UserError('Không tìm thấy Sổ nhật ký thu hộ của %s' % company_sci.name)
                journal_internal_pay_a = company_a.sudo().journal_internal_pay_id
                if not journal_internal_pay_a:
                    raise UserError('Không tìm thấy Sổ nhật ký chi hộ của %s' % company_a.name)
                journal_internal_pay_b = company_b.sudo().journal_internal_pay_id
                if not journal_internal_pay_b:
                    raise UserError('Không tìm thấy Sổ nhật ký chi hộ của %s' % company_b.name)
                journal_internal_pay_sci = company_sci.sudo().journal_internal_pay_id
                if not journal_internal_pay_sci:
                    raise UserError('Không tìm thấy Sổ nhật ký chi hộ của %s' % company_sci.name)
                if not company_a.x_internal_payable_account_id:
                    raise UserError('Không tìm thấy Tài khoản phải trả nội bộ của công ty %s' % company_a.name)
                if not company_b.x_internal_payable_account_id:
                    raise UserError('Không tìm thấy Tài khoản phải trả nội bộ của công ty %s' % company_b.name)
                #-----------------------//------------------------
                #nghiệp vụ thu hộ
                if payment.internal_payment_type == 'thu_ho':
                    # cập nhật bút toán thu hộ ở vị thế cty A
                    move_line_credit = payment.move_line_ids.filtered(lambda l: l.credit > 0)
                    move_line_debit = payment.move_line_ids.filtered(lambda l: l.debit > 0)
                    move_line_credit.sudo().update({
                        'account_id': acc_payable_a.id,
                        'partner_id': company_b.partner_id.id,
                    })
                    move_line_debit.sudo().update({
                        'partner_id': payment.company_id.partner_id.id,
                        'account_id': payment.journal_id.default_debit_account_id.id,
                    })
                    move_line_debit.move_id.x_content_payment = payment.communication
                    # tạo thêm bút toán thu hộ ở vị thế cty A
                    account_credit_id = acc_payable_a
                    account_id_debit = acc_payable_a
                    partner_credit = company_sci.partner_id
                    partner_debit = company_b.partner_id
                    move_argvs = []
                    move_argvs = payment.get_account_move_vals(account_credit_id, account_id_debit,
                                                               company_a, partner_credit, partner_debit, journal_internal_collect_a)
                    move_a = Move_Obj.create(move_argvs)
                    move_a.x_content_payment = payment.communication
                    move_a.post()

                    # tạo bút toán thu ở vị thế cty B
                    # - bút toán có
                    account_credit_id = acc_receivable_b
                    partner_credit = payment.crm_id.partner_id if payment.crm_id.partner_id else payment.partner_id
                    # - bút toán nợ
                    account_id_debit = acc_internal_trasf_b
                    partner_debit = payment.company_id.partner_id
                    move_argvs = []
                    move_argvs = payment.get_account_move_vals(account_credit_id, account_id_debit, company_b, partner_credit, partner_debit, journal_internal_collect_b)
                    move_b1 = Move_Obj.create(move_argvs)
                    move_b1.x_content_payment = payment.communication
                    move_b1.company_id = company_b.id

                    # tạo thêm bút toán thu ở vị thế cty B
                    account_credit_id = acc_internal_trasf_b
                    account_id_debit = acc_payable_b
                    partner_credit = payment.company_id.partner_id
                    partner_debit = company_sci.partner_id
                    move_argvs = []
                    move_argvs = payment.get_account_move_vals(account_credit_id, account_id_debit,
                                                               company_b, partner_credit, partner_debit, journal_internal_collect_b)
                    move_b2 = Move_Obj.create(move_argvs)
                    move_b2.x_content_payment = payment.communication
                    move_b2.company_id = company_b.id

                    #tạo bút toán ở vị thế cty SCI
                    account_credit_id = acc_internal_trasf_sci
                    account_id_debit = acc_internal_trasf_sci
                    partner_credit = company_b.partner_id
                    partner_debit = payment.company_id.partner_id
                    move_argvs = []
                    move_argvs = payment.get_account_move_vals(account_credit_id, account_id_debit,
                                                               company_sci, partner_credit, partner_debit, journal_internal_collect_sci)
                    move_sci = Move_Obj.create(move_argvs)
                    move_sci.x_content_payment = payment.communication
                    move_sci.company_id = company_sci.id
                #------------------//---------------------
                #nghiệp vụ chi hộ
                if payment.internal_payment_type == 'chi_ho':
                    #1A
                    # cập nhật bút toán thu hộ ở vị thế cty A -- Thục anh yêu cầu chỉnh sửa sao cho chỉ sinh ra 5 bút toán
                    move_line_credit = payment.move_line_ids.filtered(lambda l: l.credit > 0)
                    move_line_debit = payment.move_line_ids.filtered(lambda l: l.debit > 0)
                    move_line_credit.sudo().update({
                        'account_id': payment.journal_id.default_debit_account_id.id,
                        'partner_id': payment.partner_id.id,
                    })
                    move_line_debit.sudo().update({
                        'partner_id': company_b.partner_id.id,
                        'account_id': company_a.internal_transfer_account.id,
                    })
                    move_line_debit.move_id.ref = 'Hạch toán chi phí chi tiền'
                    move_line_debit.move_id.x_content_payment = payment.communication
                    #2A
                    account_credit_id = company_a.internal_transfer_account
                    partner_credit = company_b.partner_id

                    account_id_debit = company_a.x_internal_payable_account_id
                    partner_debit = company_sci.partner_id
                    move_argvs = []
                    move_argvs = payment.get_account_move_vals(account_credit_id, account_id_debit,
                                                               company_a, partner_credit, partner_debit, journal_internal_pay_a)
                    move_a2 = Move_Obj.create(move_argvs)
                    move_a2.ref = f'Xử lý netofff công ty {company_a.name} và {company_sci.name}'
                    move_a2.x_content_payment = payment.communication
                    move_a2.post()

                    #1B
                    account_credit_id = company_b.x_internal_payable_account_id
                    partner_credit = company_a.partner_id
                    account_id_debit = payment.partner_id.with_context(force_company=company_b.id).property_account_payable_id
                    partner_debit = payment.partner_id
                    move_argvs = []
                    move_argvs = payment.get_account_move_vals(account_credit_id, account_id_debit,
                                                               company_b, partner_credit, partner_debit, journal_internal_pay_b)
                    move_b1 = Move_Obj.create(move_argvs)
                    move_b1.company_id = company_b.id
                    move_b1.x_content_payment = payment.communication
                    move_b1.ref = 'Hạch toán công nợ nội bộ'

                    #2B
                    account_credit_id = company_b.x_internal_payable_account_id
                    partner_credit = company_sci.partner_id
                    account_id_debit = company_b.x_internal_payable_account_id
                    partner_debit = company_a.partner_id
                    move_argvs = []
                    move_argvs = payment.get_account_move_vals(account_credit_id, account_id_debit,
                                                               company_b, partner_credit, partner_debit, journal_internal_pay_b)
                    move_b2 = Move_Obj.create(move_argvs)
                    move_b2.company_id = company_b.id
                    move_b2.x_content_payment = payment.communication
                    move_b2.ref = f'Xử lý netofff công ty {company_b.name} và {company_sci.name}'

                    #1SCI
                    account_credit_id = company_sci.internal_transfer_account
                    partner_credit = company_a.partner_id
                    account_id_debit = company_sci.internal_transfer_account
                    partner_debit = company_b.partner_id
                    move_argvs = []
                    move_argvs = payment.get_account_move_vals(account_credit_id, account_id_debit,
                                                               company_sci, partner_credit, partner_debit,
                                                               journal_internal_pay_sci)
                    move_sci = Move_Obj.create(move_argvs)
                    move_sci.company_id = company_sci.id
                    move_sci.x_content_payment = payment.communication
                    move_sci.ref = f'Netoff tại {company_sci.name}'
                # ------------------//---------------------
            return rec

    def get_account_move_vals(self, account_credit_id, account_id_debit, company_id, partner_credit, partner_debit, journal_id):
        today = self.payment_date
        return {
            'journal_id': journal_id.id,
            'date': today,
            'type': 'entry',
            'invoice_date': today,
            'invoice_date_due': today,
            'company_id': company_id.id,
            'currency_id': self.currency_id.id,
            'lydo': self.communication,
            'line_ids': [
                (0, 0, self.get_account_move_line_vals(partner_id=partner_credit.id,
                                                       account_id=account_credit_id.id,
                                                       company_id=company_id.id,
                                                       currency_id=self.currency_id.id if self.currency_id != company_id.currency_id else False,
                                                       credit=self.amount_vnd,
                                                       amount_currency=-1 * abs(self.amount))),
                (0, 0, self.get_account_move_line_vals(partner_id=partner_debit.id,
                                                       account_id=account_id_debit.id,
                                                       company_id=company_id.id,
                                                       currency_id=self.currency_id.id if self.currency_id != company_id.currency_id else False,
                                                       debit=self.amount_vnd,
                                                       amount_currency=abs(self.amount)))
            ]
        }

    def get_account_move_line_vals(self, partner_id, account_id, company_id, currency_id, credit=0, debit=0, name='', amount_currency=0):
        return {
            'partner_id': partner_id,
            'account_id': account_id,
            'credit': credit,
            'debit': debit,
            'name': name,
            'company_id': company_id,
            'currency_id': currency_id,
            'amount_currency': amount_currency,
        }
