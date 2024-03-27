from odoo import fields, models, api


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


class InternalDebt(models.TransientModel):
    _name = 'account.internal.debt'
    _description = 'Description'
    _inherit = 'money.mixin'

    internal_date = fields.Date(string='Date', default=fields.Date.context_today, required=True, readonly=True,
                                copy=False, tracking=True)
    payment_id = fields.Many2one('account.payment', 'Phiếu thanh toán')
    company_id = fields.Many2one('res.company', related='payment_id.company_id', string='Cơ sở thu hộ')
    company2_id = fields.Many2one('res.company', related='payment_id.company2_id', string='Cơ sở tạo Booking')
    journal_id = fields.Many2one('account.journal', string='Sổ nhật ký', domain="[('company_id', '=', company_id)]")
    journal2_id = fields.Many2one('account.journal', string='Sổ nhật ký', compute='_get_journal')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  related='company_id.currency_id')
    amount = fields.Monetary(string='Amount', required=True, readonly=True, tracking=True)
    communication = fields.Char(string='Memo', readonly=True)
    text_amount = fields.Text('Số tiền bằng chữ', compute='get_text_amount')

    @api.depends('company2_id')
    def _get_journal(self):
        self.journal2_id = self.env['account.journal'].sudo().search([('company_id', '=', self.company2_id.id), ('name', '=ilike', 'Sổ phải thu nội bộ')], limit=1)

    @api.onchange('amount')
    def get_text_amount(self):
        self.currency_id = False
        # quy đổi tiền về tiền việt
        self.text_amount = self.num2words_vnm(round(self.amount)) + " đồng"

    # @api.depends_context('force_company')
    def request_internal_debt(self):
        # TODO tạo account.move tại công ty A và account.move tại công ty B

        for rec in self:
            AccountMove = self.env['account.move'].sudo().with_context(default_type='entry')
            # Thông tin bệnh nhân.
            patient = self.env['sh.medical.patient'].sudo().search([('partner_id', '=', rec.payment_id.partner_id.id)], limit=1)
            # Thông tin sổ nhật ký của bên đề nghị thu hộ.
            journal_id_2 = self.env['account.journal'].sudo().search([('code', '=', 'PTNB'), ('company_id', '=', rec.company2_id.id)], limit=1)
            # Đối tượng partner theo bên thu hộ
            # partner_by_company_id = self.env['res.partner'].search([('id', '=', rec.company_id.partner_id.id)], limit=1)

            company_acc_move_vals = {'patient': patient.id or '',
                                     'date': rec.internal_date,
                                     'ref': rec.payment_id.name,
                                     'journal_id': rec.journal_id.id,
                                     'company_id': rec.company_id.id,
                                     'company2_id': rec.company2_id.id,
                                     'line_ids': [(0, 0, {'account_id': rec.company_id.partner_id.property_account_payable_id.id,
                                                          # Tài khoản ghi nợ
                                                          'partner_id': rec.company2_id.partner_id.id,  # Đối tượng
                                                          'name': rec.communication,
                                                          'debit': rec.amount,
                                                          'credit': 0.0}),
                                                  (0, 0, {'account_id': rec.journal_id.default_credit_account_id.id,
                                                          # Tài khoản ghi có
                                                          'partner_id': rec.company2_id.partner_id.id,  # Đối tượng
                                                          'name': rec.communication,
                                                          'debit': 0.0,
                                                          'credit': rec.amount})
                                                  ]}
            AccountMove.create(company_acc_move_vals)

            partner = self.sudo().env['res.partner'].search([('id', '=', rec.payment_id.crm_id.partner_id.id)], limit=1)
            account_partner = partner.with_context(force_company=rec.company2_id.id).property_account_receivable_id

            company_2_acc_move_vals = {'patient': patient.id or '',
                                       'date': rec.internal_date,
                                       'ref': rec.payment_id.name,
                                       'journal_id': journal_id_2.id,
                                       'company_id': rec.company2_id.id,
                                       'company2_id': rec.company_id.id,
                                       'line_ids': [(0, 0, {'account_id': journal_id_2.default_debit_account_id.id,
                                                            # Tài khoản ghi nợ
                                                            'partner_id': rec.company_id.partner_id.id,  # Đối tượng
                                                            'name': rec.communication,
                                                            'debit': rec.amount,
                                                            'credit': 0.0}),
                                                    (0, 0, {'account_id': account_partner.id,  # Tài khoản ghi có
                                                            'partner_id': rec.payment_id.partner_id.id,  # Đối tượng
                                                            'name': rec.communication,
                                                            'debit': 0.0,
                                                            'credit': rec.amount})
                                                    ]}

            AccountMove.create(company_2_acc_move_vals)

            payments = self.env['account.payment'].search([('company_id', '=', self.payment_id.company_id.id),
                                                           ('company2_id', '=', self.payment_id.company2_id.id),
                                                           ('payment_type', '=', 'inbound'),
                                                           ('walkin', '=', self.payment_id.walkin.id),
                                                           ('state', '=', 'posted')])
            for pay in payments:
                pay.write({'state': 'sent'})

            self.payment_id.payment_ids.write({'state': 'sent'})

            rec_account_move = self.env['account.move'].search([('ref', '=', rec.payment_id.name), ('company_id', '=', rec.company_id.id)])
            rec_account_move.write({'state': 'sent'})
        return True
