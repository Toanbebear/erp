from odoo import fields, models, api, _


class TypeCrm(models.Model):
    _name = 'crm.type'
    _description = 'CRM type'

    name = fields.Char('Name')
    type_crm = fields.Selection([('lead', 'Lead'), ('opportunity', 'Opportunity')], string='Type')
    phone_call = fields.Boolean('Phone call')
    stage_id = fields.Many2many('crm.stage', 'stage_type_crm_ref', 'type_crm', 'stage', string='Stage')
    number_of_effective_day_1 = fields.Integer('Number of effective day (A)', help="Booking date - A")
    number_of_effective_day_2 = fields.Integer('Number of effective day (B)', help="Booking date + B")
