from odoo import fields, models


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    service_room_page = fields.Many2one('sh.medical.health.center.ot', string='Phòng khám')
    service_room_question = fields.Many2one(related='page_id.service_room_page')
