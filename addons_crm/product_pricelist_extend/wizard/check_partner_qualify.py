from datetime import datetime, date, timedelta
from odoo import fields, api, models, _


class CheckPartnerAndQualify(models.TransientModel):
    _inherit = 'check.partner.qualify'

    def create_line_booking(self, list_line, booking):
        for rec in list_line:
            line = self.env['crm.line'].create({
                'name': rec.name,
                'quantity': rec.quantity,
                'is_treatment': rec.is_treatment,
                'number_used': rec.number_used,
                'unit_price': rec.unit_price,
                'discount_percent': rec.discount_percent,
                'type': rec.type,
                'discount_cash': rec.discount_cash,
                'sale_to': rec.sale_to,
                'price_list_id': rec.price_list_id.id,
                'total_before_discount': rec.total_before_discount,
                'crm_id': booking.id,
                'company_id': rec.company_id.id,
                'product_id': rec.product_id.id,
                'teeth_ids': [(6, 0, rec.teeth_ids.ids)],
                'source_extend_id': rec.source_extend_id.id,
                'line_booking_date': booking.booking_date,
                'status_cus_come': 'no_come',
                'uom_price': rec.uom_price,
                'prg_ids': [(6, 0, rec.prg_ids.ids)],
                'consultants_1': rec.consultants_1.id,
                'consultants_2': rec.consultants_2.id,
                'consulting_role_1': rec.consulting_role_1,
                'consulting_role_2': rec.consulting_role_2,
                'crm_information_ids': [(6, 0, rec.crm_information_ids.ids)],
                'price_min': rec.price_min
            })
            crm_line_discount_history = self.env['crm.line.discount.history'].search(
                [('booking_id', '=', self.lead_id.id), ('crm_line', '=', rec.id)])
            for record in crm_line_discount_history:
                self.env['crm.line.discount.history'].create({
                    'booking_id': booking.id,
                    'discount_program': record.discount_program.id,
                    'type': record.type,
                    'discount': record.discount,
                    'crm_line': line.id,
                    'index': record.index,
                    'type_discount': record.type_discount
                })
