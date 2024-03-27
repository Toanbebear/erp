# from odoo import fields, models, api
#
#
# class ShWalkinEvaluation(models.Model):
#     _inherit = 'sh.medical.evaluation'
#
#     check_state = fields.Selection([('1', 'Có'), ('2', 'Không')], string='Khảo sát', compute='on_change', store="True")
#
#     @api.depends('surgery_history_survey_ids')
#     def on_change(self):
#         for rec in self:
#             rec.check_state = '2'
#             if rec.surgery_history_survey_ids:
#                 rec.check_state = '1'
