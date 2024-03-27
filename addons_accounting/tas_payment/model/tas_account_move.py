# -*- coding: utf-8 -*-

from num2words import num2words

from odoo import fields, models, api
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    tas_type = fields.Selection([
        ('inbound', 'Phiếu Thu'),
        ('outbound', 'Phiếu Chi'),
        ('debit', 'Giấy báo nợ'),
        ('credit', 'Giấy báo có'),
        ('other', 'Chứng từ kế toán'),
    ], 'Loại Phiếu', default='other')

    money_char = fields.Char("Tiền ghi bằng chữ", compute='_compute_tien_bang_chu')
    ma_phieu_in = fields.Char("Mã Phiếu In")
    origin = fields.Char('Chứng từ gốc')
    kemtheo = fields.Integer("Kèm theo")
    lydo = fields.Char("Lý do")
    address = fields.Char("Địa chỉ")
    nguoi_lap = fields.Many2one("res.users", string="Người lập")
    nguoi_nhan = fields.Many2one("res.partner", "Người nộp tiền/nhận tiền")
    nguoi_nhan_char = fields.Char("Người nộp tiền/nhận tiền (nhập)", help='Nhập giá trị người nhận/nộp tiền nếu không tìm thấy ở trường Người nộp tiền/nhận tiền')
    manager_id = fields.Many2one("res.users", string="Tổng giám đốc")
    accountant_id = fields.Many2one("res.users", string="Kế toán trưởng")
    treasurer_id = fields.Many2one("res.users", string="Thủ quỹ")
    team_id = fields.Many2one(
        'crm.team', related='invoice_user_id.sale_team_id', store=True)
    payment_id = fields.Many2one('account.payment', "Phiếu thanh toán AP")
    warning_note = fields.Text("Cảnh báo", default="")
    is_warning = fields.Boolean("Check cảnh báo", compute="_check_warning_invoice")

    def action_create_ma_phieu(self):
        if not self.manager_id:
            self.manager_id = self.journal_id.manager_id
        if not self.accountant_id:
            self.accountant_id = self.journal_id.accountant_id
        if not self.treasurer_id:
            self.treasurer_id = self.journal_id.treasurer_id
        if len(self.payment_id) > 0:
            if self.payment_id.payment_type == 'inbound':
                if self.payment_id.journal_id.type == 'cash':
                    self.tas_type = 'inbound'
                else:
                    self.tas_type = 'credit'
            if self.payment_id.payment_type == 'outbound':
                if self.payment_id.journal_id.type == 'cash':
                    self.tas_type = 'outbound'
                else:
                    self.tas_type = 'debit'

        if self.tas_type == 'inbound' or self.tas_type == 'credit':
            self.ma_phieu_in = self.journal_id.pt_sequence_id.next_by_id()

        if self.tas_type == 'outbound' or self.tas_type == 'debit':
            self.ma_phieu_in = self.journal_id.pc_sequence_id.next_by_id()

    @api.depends('tas_type')
    def _check_warning_invoice(self):
        for record in self:
            if record.tas_type != 'other':
                list_accounts = []
                debit_account_lines = []
                credit_account_lines = []
                for line in record.line_ids:
                    list_accounts.append(line.account_id)
                    if line.debit > 0:
                        debit_account_lines.append(line.account_id)
                    else:
                        credit_account_lines.append(line.account_id)

                if (record.journal_id.default_debit_account_id not in list_accounts) or (record.journal_id.default_credit_account_id not in list_accounts):

                    record.is_warning = True
                    record.warning_note = "Cảnh báo các tài khoản trong bút toán sai so với sổ nhật ký"
                else:
                    record.is_warning = False
                    record.warning_note = ""

                # Neu la thu tien
                if record.tas_type in ('inbound', 'credit'):
                    if (record.journal_id.default_debit_account_id in credit_account_lines) or (
                            record.journal_id.default_credit_account_id in credit_account_lines):
                        record.is_warning = True
                        if record.warning_note == "":
                            record.warning_note = "Cảnh báo Phiếu thu - Giấy báo có đang ghi bút toán bên có"
                        else:
                            record.warning_note += "\nCảnh báo Phiếu thu - Giấy báo có đang ghi bút toán bên có"

                if record.tas_type in ('outbound', 'debit'):
                    if (record.journal_id.default_debit_account_id in debit_account_lines) or (
                            record.journal_id.default_credit_account_id in debit_account_lines):
                        record.is_warning = True
                        if record.warning_note == "":
                            record.warning_note = "Cảnh báo Phiếu chi - Giấy báo nợ đang ghi bút toán bên nợ"
                        else:
                            record.warning_note += "\nCảnh báo Phiếu chi - Giấy báo nợ đang ghi bút toán bên nợ"

            else:
                record.is_warning = False
                record.warning_note = ""

    @api.depends('amount_total')
    def _compute_tien_bang_chu(self):
        for record in self:
            try:
                currency_unit_label = record.currency_id.currency_unit_label if record.currency_id and record.currency_id.currency_unit_label else ''
                record.money_char = num2words(
                    record.amount_total, lang='vi_VN').capitalize() + " " + currency_unit_label + " chẵn."
            except NotImplementedError:
                record.money_char = num2words(
                    record.amount_total, lang='en').capitalize() + " VND."

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        super(AccountMove, self)._compute_suitable_journal_ids()

        for m in self:
            if m.tas_type in ('inbound', 'outbound', 'debit', 'credit'):
                domain = [('company_id', '=', m.company_id.id),
                          ('type', 'in', ['general', 'bank', 'cash'])]
                m.suitable_journal_ids = self.env['account.journal'].search(domain)

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        if res.journal_id.type in ('bank', 'cash'):
            if res.is_warning:
                raise UserError(res.warning_note)
            else:
                if res.tas_type != 'other' and res.journal_id.id:
                    res.action_create_ma_phieu()
                return res
        else:
            return res
    # def write(self, vals):
    #     # res = super(AccountMove, self).write(vals)
    #     if 'warning_note' in vals:
    #         if len(vals['warning_note']) > 0:
    #             raise UserError(vals['warning_note'])
    #         else:
    #             return super(AccountMove, self).write(vals)
    #
    #     return super(AccountMove, self).write(vals)
    #     # else:
    #     #     return res