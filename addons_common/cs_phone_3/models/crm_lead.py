# -*- coding: utf-8 -*-
#############################################################################
#
#    SCI SOFTWARE
#
#    Copyright (C) 2019-TODAY SCI Software(<https://www.scisoftware.xyz>)
#    Author: SCI Software(<https://www.scisoftware.xyz>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
from odoo.exceptions import ValidationError

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    phone_no_3 = fields.Char('Điện thoại 3')

    def update_partner(self, vals):
        res = super(CrmLead, self).update_partner(vals)
        if self.partner_id:
            partner = self.partner_id
            if ('phone_no_3' in vals) and vals['phone_no_3'] and partner.phone_no_3 != vals['phone_no_3']:
                partner.phone_no_3 = vals['phone_no_3']
                if self.lead_id and (self.lead_id.type == 'lead'):
                    self.lead_id.phone_no_3 = vals['phone_no_3'] if self.lead_id.phone_no_3 != vals['phone_no_3'] else self.lead_id.phone_no_3
        return res

    @api.constrains('phone_no_3')
    def phone_no_3_constrains(self):
        if self.phone_no_3:
            if self.phone_no_3.isdigit() is False:
                raise ValidationError('Trường ĐIỆN THOẠI 3 chỉ nhận giá trị số')

    @api.constrains('phone_no_3')
    def check_phone_no_3(self):
        for rec in self:
            if rec.phone_no_3:
                if rec.phone_no_3.isdigit() is False:
                    raise ValidationError('Điện thoại 3 chỉ nhận giá trị số')
                elif rec.phone_no_3:
                    if rec.mobile == rec.phone_no_3 or rec.phone == rec.phone_no_3:
                        raise ValidationError('Điện thoại 3 không được trùng với số điện thoại 1 hoặc số điện thoại 2')

    @api.onchange('phone')
    def check_partner_lead(self):
        res = super(CrmLead, self).check_partner_lead()
        if not self.env.context.get('default_phone') and self.type == 'lead' and self.stage_id != self.env.ref(
                'crm_base.crm_stage_re_open'):
            partner = self.env['res.partner'].search([('phone', '=', self.phone)], limit=1)

            lead_ids = self.env['crm.lead'].search(
                [('phone', '=', self.phone), ('brand_id', '=', self.brand_id.id)], order="id asc", limit=1)
            if partner:
                self.phone_no_3 = partner.phone_no_3
            else:
                self.phone_no_3 = lead_ids.phone_no_3
        return res

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(CrmLead, self).fields_get(allfields, attributes=attributes)
        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone_no_3']:
                fields[field_name]['exportable'] = False
        return fields

    def update_info(self):
        res = super(CrmLead, self).update_info()
        if self.booking_ids:
            for rec in self.booking_ids:
                rec.write({
                    'phone_no_3': self.phone_no_3,
                })
        if self.partner_id:
            self.partner_id.write({
                'phone_no_3': self.phone_no_3,
            })
        return res


class CheckPartnerAndQualify(models.TransientModel):
    _inherit = 'check.partner.qualify'

    def qualify(self):
        res = super(CheckPartnerAndQualify, self).qualify()
        booking = self.env['crm.lead'].browse(int(res['res_id']))
        phone_no_3 = False
        if booking:
            if booking.lead_id and booking.lead_id.phone_no_3:
                phone_no_3 = booking.lead_id.phone_no_3
            else:
                phone_no_3 = booking.partner_id.phone_no_3 if booking.partner_id.phone_no_3 else False
        booking.sudo().write({
            'phone_no_3': phone_no_3
        })

        return res
