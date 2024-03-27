# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class BenhNhan(models.Model):
    _inherit = 'sh.medical.patient'

    """ Bổ sung chỉ mục cho model """
    # Bác sỹ
    doctor = fields.Many2one(index=True)

    partner_id = fields.Many2one(index=True)

    # his_company_ids = fields.Many2many('res.company', 'sh_medical_patient_company_related_rel',
    #                                'patient_id', 'company_id',
    #                                string='Chi nhánh',
    #                                related="walkin.institution.his_company",
    #                                store=True,
    #                                readonly=True,
    #                                ondelete='cascade')
