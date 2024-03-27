from odoo import api, fields, models


class SurveyLabel(models.Model):
    _inherit = 'survey.label'

    value_description = fields.Char(string='Định nghĩa', help='Định nghĩa cho mỗi đáp án của câu hỏi')
