import datetime
from odoo.exceptions import ValidationError

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
import datetime

class AddServiceGuaranteeLine(models.TransientModel):
    _inherit = 'add.service.guarantee.line'

    reason_id = fields.Many2one('crm.guarantee.reason', string='Lí do bảo hành')
    TYPE_GUARANTEE = [('not_totality', 'Một phần'), ('totality', 'Toàn phần')]
    type_guarantee_2 = fields.Selection(TYPE_GUARANTEE,
                                        help='Trường này dành cho Booking bảo hành', string='Loại bảo hành')
    product_incurred_2 = fields.Many2one('product.product', string='Dịch vụ phát sinh')
    checked = fields.Boolean('Checked')

    @api.onchange('add_service_guarantee_id')
    def onchange_brand_id(self):
        if self.add_service_guarantee_id.pricelist_incurred:
            domain = []
            brand_id = self.add_service_guarantee_id.brand_id
            price_list = self.add_service_guarantee_id.pricelist_incurred
            if price_list:
                domain += [('id', 'in', price_list.item_ids.mapped('product_id').ids)]
            return {'domain': {'product_incurred_2': [('id', 'in', self.env['product.product'].sudo().search(domain).ids if domain else [])]}}
        else:
            return {'domain': {'product_incurred_2': [('id', '=', 0)]}}
    @api.onchange('type_guarantee_2')
    def onchange_type_guarantee(self):
        domain = []
        if self.type_guarantee_2:
            if self.type_guarantee_2 == 'not_totality':
                domain += [('not_totality', '=', True)]
            elif self.type_guarantee_2 == 'totality':
                domain += [('totality', '=', True)]
            reason_id = self.env['crm.guarantee.reason'].search(domain)
            return {'domain': {'reason_id': [('id', 'in', reason_id.ids)]}}
        else:
            return {'domain': {'reason_id': [('id', 'in', [])]}}
class AddServiceGuarantee(models.TransientModel):
    _inherit = 'add.service.guarantee'

    def confirm_create(self):
        if self.add_service_line_guarantee:
            for service_line in self.add_service_line_guarantee:
                if service_line.product_incurred_2 and self.pricelist_incurred:
                    if self.pricelist_incurred:
                        crm_information_ids = []
                        if self.crm_id.brand_id.id == 3:
                            crm_information_id = self.env['crm.information.consultant'].sudo().create(
                                {'role': 'recept', 'user_id': self.env.user.id})
                            crm_information_ids.append(crm_information_id.id)
                        value = {
                            'product_id': service_line.product_incurred_2.id,
                            'quantity': 1,
                            'price_list_id': self.pricelist_incurred.id,
                            'unit_price': self.env['product.pricelist.item'].search(
                                [('pricelist_id', '=', self.pricelist_incurred.id),('product_id', '=', service_line.product_incurred_2.id)]).fixed_price,
                            'crm_id': self.crm_id.id,
                            'company_id': self.crm_id.company_id.id,
                            'source_extend_id': self.crm_id.source_id.id,
                            'line_booking_date': datetime.datetime.now(),
                            'status_cus_come': 'no_come',
                            'consultants_1': self.env.user.id if self.crm_id.brand_id != 3 else None,
                            'crm_information_ids': [(6, 0, crm_information_ids)],
                            'initial_product_id': service_line.crm_line_guarantee.product_id.id,
                            'reason_guarantee_id': service_line.reason_id.id,
                            'type_guarantee_2': service_line.type_guarantee_2,
                        }
                        if self.brand_id.type == 'hospital':
                            service_id = self.env['sh.medical.health.center.service'].search(
                                [('product_id', '=', service_line.product_incurred_2.id)])
                            if service_id:
                                value['service_id'] = service_id.id
                        self.env['crm.line'].create(value)
                    else:
                        raise ValidationError('Bạn chưa chọn bảng giá')
                else:
                    crm_information_ids = []
                    if self.crm_id.brand_id.id == 3:
                        crm_information_id = self.env['crm.information.consultant'].sudo().create(
                            {'role': 'recept', 'user_id': self.env.user.id})
                        crm_information_ids.append(crm_information_id.id)
                    value = {
                        'product_id': service_line.crm_line_guarantee.product_id.id,
                        'quantity': 1,
                        'price_list_id': self.crm_id.price_list_id.id,
                        'unit_price': self.env['product.pricelist.item'].search(
                            [('pricelist_id', '=', self.crm_id.price_list_id.id),
                             ('product_id', '=', service_line.crm_line_guarantee.product_id.id)]).fixed_price,
                        'crm_id': self.crm_id.id,
                        'company_id': self.crm_id.company_id.id,
                        'source_extend_id': self.crm_id.source_id.id,
                        'line_booking_date': datetime.datetime.now(),
                        'status_cus_come': 'no_come',
                        'uom_price': service_line.crm_line_guarantee.uom_price,
                        'initial_product_id': service_line.crm_line_guarantee.product_id.id,
                        'reason_guarantee_id': service_line.reason_id.id,
                        'type_guarantee_2': service_line.type_guarantee_2,
                        'consultants_1': self.env.user.id,
                        'crm_information_ids': [(6, 0, crm_information_ids)]
                    }
                    if self.brand_id.type == 'hospital':
                        value['service_id'] = service_line.crm_line_guarantee.service_id.id
                    self.env['crm.line'].create(value)
        else:
            raise ValidationError('Chưa có giá trị tại bảng quy đổi dịch vụ bảo hành')
