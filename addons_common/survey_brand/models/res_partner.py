# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    survey_input_ids = fields.One2many('survey.user_input', 'partner_id', string='Surveys')
    survey_input_count = fields.Integer('Survey Count', compute='_compute_survey_input_count')

    def _compute_survey_input_count(self):
        read_group_var = self.env['survey.user_input'].read_group(
            [('partner_id', 'in', self.ids)],
            fields=['partner_id'],
            groupby=['partner_id'])

        survey_input_count_dict = dict((d['partner_id'][0], d['partner_id_count']) for d in read_group_var)
        for record in self:
            record.survey_input_count = survey_input_count_dict.get(record.id, 0)

    def action_see_surveys(self):
        self.ensure_one()
        return {
            'name': _('Survey'),
            'res_model': 'survey.user_input',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('survey_brand.survey_user_input_view_tree').id,
            'context': {
                "search_default_partner_id": self.id,
                "default_partner_id": self.id,
            },
        }
    #
    # def action_view_partner_invoices(self):
    #     self.ensure_one()
    #     action = self.env.ref('account.action_move_out_invoice_type').read()[0]
    #     action['domain'] = [
    #         ('type', 'in', ('out_invoice', 'out_refund')),
    #         ('state', '=', 'posted'),
    #         ('partner_id', 'child_of', self.id),
    #     ]
    #     action['context'] = {'default_type':'out_invoice', 'type':'out_invoice', 'journal_type': 'sale', 'search_default_unpaid': 1}
    #     return action
    #
    #
    #
    #
    #
    # def _compute_document_count(self):
    #     read_group_var = self.env['documents.document'].read_group(
    #         [('partner_id', 'in', self.ids)],
    #         fields=['partner_id'],
    #         groupby=['partner_id'])
    #
    #     document_count_dict = dict((d['partner_id'][0], d['partner_id_count']) for d in read_group_var)
    #     for record in self:
    #         record.document_count = document_count_dict.get(record.id, 0)