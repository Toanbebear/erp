import datetime

from odoo import fields, models, api


class CancelCRMLine(models.TransientModel):
    _name = 'crm.advise.cancel'
    _description = 'Cancel CRM Advise'

    crm_line_id = fields.Many2one('crm.line', string='Dịch vụ')
    advise_id = fields.Many2one('crm.advise.line', string='Phiếu tư vấn')
    REASON_LINE_CANCEL = [('change_service', 'Đổi sang dịch vụ khác cùng nhóm'),
                          ('due_to_illness', 'Hủy do bệnh lý'), ('create_wrong_service', 'Thao tác tạo sai dịch vụ'),
                          ('not_money', 'Không đủ chi phí'), ('consultant', 'Tham khảo trước'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy dịch vụ')
    name = fields.Char('Ghi chú')
    # is_potential = fields.Boolean(string='Dịch vụ tiềm năng', default=True)

    is_potential = fields.Selection([('yes', 'Có'), ('no', 'Không')], string='Dịch vụ tiềm năng', required=True)

    def cancel_crm_advise(self):
        self.crm_line_id.stage = 'cancel'
        self.crm_line_id.gia_truoc_huy = self.crm_line_id.total
        self.crm_line_id.reverse_prg_ids()
        self.crm_line_id.reason_line_cancel = self.reason_line_cancel
        self.advise_id.reason_line_cancel = self.reason_line_cancel
        self.crm_line_id.note = self.name
        self.crm_line_id.cancel = True
        self.crm_line_id.cancel_user = self.env.user
        self.crm_line_id.cancel_date = datetime.datetime.now()
        if self.is_potential == 'yes':
            self.advise_id.conclude = "Hủy, tiềm năng"
            if self.advise_id:
                self.advise_id.is_potential = True
                self.advise_id.stage_potential = 'potential'
            if self.crm_line_id:
                self.crm_line_id.is_potential = True
        else:
            self.advise_id.conclude = "Hủy"

