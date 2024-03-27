from odoo import fields, models, api


class WalkinInherit(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    advise_ids = fields.Many2many('crm.advise.line', string='Phiếu tư vấn', compute='get_advise_line')

    @api.depends('booking_id', 'service')
    def get_advise_line(self):
        for rec in self:
            if rec.booking_id.advise_ids:
                list_advises = []
                for advise in rec.booking_id.advise_ids:
                    if advise.service in rec.service:
                        list_advises.append(advise.id)
                rec.advise_ids = [(6,0,list_advises)]
            else:
                rec.advise_ids = False
