from odoo import fields, models, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    survey_id = fields.Many2one(related='brand_id.survey_id')
    survey_kn_id = fields.Many2one('survey.survey', string='survey')



