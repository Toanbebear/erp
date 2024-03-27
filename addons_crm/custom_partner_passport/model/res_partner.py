from odoo import models, fields, api


class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'
    _description = 'Res Partner Passport'

    crm_case_ids = fields.One2many('crm.case', 'partner_id', string='Case', tracking=True)
    loyalty_card_ids = fields.One2many('crm.loyalty.card', 'partner_id', string='Thẻ thành viên', tracking=True)
    walkin_ids = fields.One2many('sh.medical.appointment.register.walkin', 'partner_id', string='Phiếu khám', tracking=True)
