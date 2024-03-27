from odoo import fields, api, models
from lxml import etree
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from datetime import datetime, date, timedelta
import json
from dateutil.relativedelta import relativedelta
import pytz


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    consultation_ticket_ids = fields.One2many('consultation.ticket', 'booking_id', string='Phiếu tư vấn')

    def open_consultation_ticket(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        return {
            "type": "ir.actions.act_url",
            "url": "%s/phieu-tu-van/%s" % (base_url, self.id),
            "target": "new"
        }

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(CRMLead, self).fields_view_get(view_id, view_type, toolbar, submenu)
    #     doc = etree.XML(res['arch'])
    #     view_booking = self.env.ref('crm_base.crm_lead_form_booking')
    #     if view_type == 'form' and view_id == view_booking.id:
    #         for node in doc.xpath("//field[@name='consultation_ticket_ids']"):
    #             node.set("readonly", "True")
    #             modifiers = json.loads(node.get("modifiers"))
    #             modifiers['readonly'] = True
    #             node.set("modifiers", json.dumps(modifiers))
    #     return res
