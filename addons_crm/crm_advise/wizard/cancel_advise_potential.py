import datetime

from odoo import fields, models, api


class CancelAdvisePotential(models.TransientModel):
    _name = 'crm.advise.cancel.potential'
    _description = 'Hủy tiềm năng'

    reason = fields.Selection([('no_service', 'Hết nhu cầu làm dịch vụ'), ('other_branch', 'Đã làm tại cơ sở khác')], string='Lí do hủy tiềm năng')
    note = fields.Char('Ghi chú')
    crm_advise_id = fields.Many2one('crm.advise.line')

    def confirm_cancel(self):
        self.crm_advise_id.stage_potential = 'cancel'
        self.crm_advise_id.reason_cancel_potential = self.reason
        self.crm_advise_id.note_cancel_potential = self.note


