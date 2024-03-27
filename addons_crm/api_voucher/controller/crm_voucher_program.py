import json

from odoo import http, _
from odoo.http import request

class CrmVoucherController(http.Controller):
    @http.route(["/create_voucher"], type='json', auth='public', methods=["POST"], csrf=False)
    def create_voucher(self, **payload):
        body = json.loads(request.httprequest.data.decode('utf-8'))
        voucher_program = request.env['crm.voucher.program'].sudo().search([('prefix', '=', body['prefix'])])
        if voucher_program:
            voucher_program.check_sequence()

