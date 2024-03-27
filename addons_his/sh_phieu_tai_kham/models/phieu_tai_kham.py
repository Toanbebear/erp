# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PhieuTaiKham(models.Model):
    _inherit = 'sh.medical.evaluation'

    company_id = fields.Many2one('res.company', string='Công ty chính',
                                 related="walkin.company_id",
                                 store=True,
                                 ondelete='cascade')

    company2_id = fields.Many2many('res.company', 'sh_medical_evaluation_company_related_rel',
                                   'evaluation_id', 'company_id',
                                   string='Công ty share',
                                   related="walkin.company2_id",
                                   store=True,
                                   readonly=True,
                                   ondelete='cascade')

    his_company = fields.Many2one('res.company', string='Công ty cơ sở y tế',
                                  related="institution.his_company",
                                  store=True,
                                  ondelete='cascade')

    # sh_user_id = fields.Many2many('res.users', 'sh_medical_evaluation_sh_user_related_rel',
    #                                'evaluation_id', 'sh_user_id',
    #                                string='Bác sĩ khoa',
    #                                compute="_compute_sh_user",
    #                                store=True,
    #                                readonly=True,
    #                                ondelete='cascade')
    #
    # @api.depends('room')
    # def _compute_sh_user(self):
    #     for record in self:
    #         if record.room and record.room.department and record.room.department.physician and record.room.department.physician.sh_user_id:
    #             record.sh_user_id = [(6, 0, record.room.department.physician.sh_user_id.ids)]
    #         else:
    #             record.sh_user_id = False

    def view_customer_persona(self):
        domain = self.env['ir.config_parameter'].sudo().get_param('domain_customer_persona_extend')
        url = domain + '/app/customer-portrait/profile?company_id=%s&partner_id=%s' % (
            self.env.company.id, self.patient.partner_id.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
