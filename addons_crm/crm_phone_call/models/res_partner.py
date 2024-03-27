from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    phone_call_ids = fields.One2many('crm.phone.call', 'partner_id', string='Phonecall')
    sms_ids = fields.One2many('crm.sms', 'partner_id', string='SMS')
    walkin_ids = fields.One2many('sh.medical.appointment.register.walkin', 'partner_id', string='Phiếu khám')
    crm_case_ids = fields.One2many('crm.case', 'partner_id', string='Case', tracking=True)
