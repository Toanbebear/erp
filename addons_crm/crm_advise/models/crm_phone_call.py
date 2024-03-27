from odoo import models, fields, api


class CrmPhoneCall(models.Model):
    _inherit = 'crm.phone.call'

    advise_line_id = fields.Many2one('crm.advise.line', string='Dịch vụ tiềm năng')
    doctor = fields.Many2one('sh.medical.physician', string="Bs thực hiện", related='medical_id.doctor')

    @api.depends('crm_id', 'advise_line_id')
    def get_crm_line(self):
        for rec in self:
            if rec.advise_line_id:
                if rec.advise_line_id.crm_line_id:
                    rec.crm_line_id = [(6, 0, rec.advise_line_id.crm_line_id.ids)]
                else:
                    rec.crm_line_id = False
            else:
                rec.crm_line_id = [(6, 0, rec.crm_id.crm_line_ids.ids)]
