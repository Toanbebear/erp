# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class ChamSocHauPhau(models.Model):
    _inherit = 'sh.medical.patient.rounding'

    """ Bổ sung chỉ mục cho model """
    patient = fields.Many2one(index=True)
    # Mã lưu bệnh nhân
    inpatient_id = fields.Many2one(index=True)
    name = fields.Char(index=True)

    # Bác sỹ
    doctor = fields.Many2one(index=True)

    # Điều dưỡng
    physician = fields.Many2one(index=True)
    evolution = fields.Selection(index=True)
    state = fields.Selection(index=True)

    """ Thêm trường tăng tốc rule """
    his_company = fields.Many2one('res.company', string='Công ty cơ sở y tế',
                                  related="inpatient_id.institution.his_company",
                                  store=True,
                                  ondelete='cascade')
