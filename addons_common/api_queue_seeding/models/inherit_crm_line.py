from odoo import fields, api, models


class InheritCrmLine(models.Model):
    _inherit = 'crm.line'

    date_done = fields.Datetime('Ngày hoàn thành dịch vụ', compute='set_date_done', store=True)

    @api.depends('number_used')
    def set_date_done(self):
        for rec in self:
            if not rec.date_done and rec.number_used == 1 and rec.id >= 1348898:
                rec.date_done = fields.datetime.now()