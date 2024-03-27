from odoo import fields, api, models
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    TYPE_PARTNER = [('old', 'Khách hàng cũ'), ('new', 'Khách hàng mới')]
    type_data_partner = fields.Selection(TYPE_PARTNER, string='Loại khách hàng')

    @api.model
    def create(self, vals_list):
        res = super(CrmLead, self).create(vals_list)
        partner = res.partner_id
        if ('sale' in partner.sudo().sale_order_ids.mapped('state')) or (
                'done' in partner.sudo().sale_order_ids.mapped('state')):
            res.type_data_partner = 'old'
            partner.type_data_partner = 'old'
        elif 'old' in partner.crm_ids.mapped('type_data_partner'):
            res.type_data_partner = 'old'
            partner.type_data_partner = 'old'
        else:
            res.type_data_partner = 'new'
            partner.type_data_partner = 'new'
        return res


# class CheckPartnerTypeData(models.TransientModel):
#     _inherit = 'check.partner.qualify'
#     _description = 'Check Partner AndQualify'

    # def qualify(self):
    #     res = super(CheckPartnerTypeData, self).qualify()
    #     booking = self.env['crm.lead'].search([('id', '=', res['res_id'])])
    #     if booking.phone and booking.partner_id:
    #         partner = booking.partner_id
    #         if ('sale' in partner.sudo().sale_order_ids.mapped('state')) or (
    #                 'done' in partner.sudo().sale_order_ids.mapped('state')):
    #             booking.type_data_partner = 'old'
    #             partner.type_data_partner = 'old'
    #         elif 'old' in partner.crm_ids.mapped('type_data_partner'):
    #             booking.type_data_partner = 'old'
    #             partner.type_data_partner = 'old'
    #         else:
    #             booking.type_data_partner = 'new'
    #             partner.type_data_partner = 'new'
    #             booking.lead_id.type_data_partner = 'new'
    #     return res

