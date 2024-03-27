# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.http import request


class SurveyQR(models.AbstractModel):
    _name = 'report.survey_base.survey_qr_template'
    _description = "Report Survey QR Template"

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'data': request.env['survey.survey'].browse(data['data'])
        }
