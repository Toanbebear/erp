from odoo import fields, models, api

class CRMBrand(models.Model):
    _inherit = 'crm.brand'
    _description = 'Crm Brand'

    survey_id = fields.Many2one('survey.survey', string='Survey')
