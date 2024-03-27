from odoo import fields, models, api

class SCIBrand(models.Model):
    _inherit = 'res.brand'

    survey_id = fields.Many2one('survey.survey', 'Survey')
