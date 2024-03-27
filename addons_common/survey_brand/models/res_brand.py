from odoo import models, fields


class ResBrand(models.Model):
    _inherit = 'res.brand'

    survey_id = fields.Many2one('survey.survey', string='Khảo sát')
