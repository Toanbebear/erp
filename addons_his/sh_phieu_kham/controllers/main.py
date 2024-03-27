"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MainController(http.Controller):

    @http.route("/reset/lab-test", type="json", auth="none", methods=["POST"], csrf=False)
    def reset_lab_test(self, walkin_id=False,  uid=False, **payload):
        walkin_id = request.env['sh.medical.appointment.register.walkin'].sudo().with_user(uid).browse(int(walkin_id))
        if walkin_id:
            walkin_id.reset_all_labtest()
        return {
            'status': walkin_id
        }

    @http.route("/add/lab-test", type="json", auth="none", methods=["POST"], csrf=False)
    def add_lab_test(self, walkin_id=False, uid=False, company_id=False, **payload):
        print('company_id')
        print(company_id)
        institution_id = request.env['sh.medical.health.center'].sudo().with_user(uid).browse(int(company_id))
        print(institution_id)
        company = institution_id.his_company
        print(company)
        walkin_id = request.env['sh.medical.appointment.register.walkin'].sudo().with_user(uid).with_context(company=company).browse(int(walkin_id))
        if walkin_id:
            walkin_id.add_config_labtest()
        return {
            'status': walkin_id
        }