# Part of odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo.addons.crm_ehc.controllers.crm_hh_ehc_common import ehc_validate_token, get_brand_id_hh

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class GetCampaignController(http.Controller):
    @ehc_validate_token
    @http.route("/api/v1/get-campaign", methods=["GET"], type="json", auth="none", csrf=False)
    def v1_ehc_get_campaign(self, **payload):
        domain = [('campaign_status', '!=', 3), ('brand_id', '=', get_brand_id_hh())]
        fields = ['id', 'name', 'brand_id']
        data = request.env['utm.campaign'].sudo().search_read(
            domain=domain, fields=fields,
        )
        if data:
            return {
                'stage': 0,
                'message': 'Lấy dữ liêu chiến dịch thành công!!!',
                'data': data
            }
        else:
            return {
                'stage': 1,
                'message': 'Lấy dữ liêu chiến dịch thất bại!!'
            }
