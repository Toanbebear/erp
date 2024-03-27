from odoo import api, models, fields
import datetime


class CancelCRMLine(models.TransientModel):
    _inherit = 'crm.line.cancel'
    is_potential = fields.Selection([('yes', 'Có'), ('no', 'Không')], string='Dịch vụ tiềm năng', required=True)

    def cancel_crm_line(self):
        self.crm_line_id.stage = 'cancel'
        self.crm_line_id.gia_truoc_huy = self.crm_line_id.total
        self.crm_line_id.reverse_prg_ids()
        self.crm_line_id.reason_line_cancel = self.reason_line_cancel
        self.crm_line_id.note = self.name
        self.crm_line_id.cancel = True
        self.crm_line_id.cancel_user = self.env.user
        self.crm_line_id.cancel_date = datetime.datetime.now()
        advise = self.env['crm.advise.line'].sudo().search([('crm_line_id','=',self.crm_line_id.id)])
        if self.is_potential == 'yes':
            self.crm_line_id.is_potential = True
            if advise:
                advise.conclude = "Hủy, tiềm năng"
                advise.is_potential = True
                advise.stage_potential = 'potential'
                self.crm_line_id.is_potential = True
        else:
            self.crm_line_id.is_potential = False
            if advise:
                advise.conclude = "Hủy"
                advise.is_potential = False
                self.crm_line_id.is_potential = False
