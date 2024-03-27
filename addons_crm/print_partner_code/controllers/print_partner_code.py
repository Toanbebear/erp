from odoo import http
from odoo.http import request


class PartnerCodeController(http.Controller):

    @http.route("/qr-booking/<string:ma_booking>", methods=["GET"], type="http", auth="none", csrf=False)
    def open_booking(self, ma_booking):
        booking = request.env['crm.lead'].sudo().search([('name', '=', ma_booking)], limit=1)
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if booking:
            url = f'{base_url}/web#id={booking.id}&view_type=form&model=crm.lead&menu_id=431'
            return request.make_response('<script>window.location.href="%s";</script>' % url)

    @http.route("/khach-hang/<int:partner_id>", methods=["GET"], type="http", auth="none", csrf=False)
    def open_partner(self, partner_id):
        partner = request.env['res.partner'].sudo().browse(partner_id)
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if partner:
            url = f'{base_url}/web#id={partner.id}&view_type=form&model=res.partner&menu_id=380'
            return request.make_response('<script>window.location.href="%s";</script>' % url)
