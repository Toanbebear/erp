from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .constant import MRP_PRODUCTION_STATE
from .constant import MRP_PRODUCTION_STATE
import json


class ProductCostMrpProductionMaterial(models.AbstractModel):
    _name = 'product.cost.mrp.production.material'
    _description = 'mrp production material'

    bom_ids = fields.Many2many('sh.medical.product.bundle', 'sh_medical_product_bundle_mo_line_rel', 'supply_id', 'bom_id', compute='_compute_bom_ids')
    service_price_ratio = fields.Char(compute='_compute_bom_ids')

    def _compute_bom_ids(self):
        pass

    def seperate_actual_price(self, phieu, services, quantity, type):

        # lines = order.order_line.read_group(domain=[('order_id', '=', order.id)],
        #                                     fields=['name', 'product_id', 'product_qty', 'price_total',
        #                                             'price_subtotal', 'price_unit'],
        #                                     groupby=['product_id'])

        bom_ids = [(5, 0, 0)]
        service_price_ratio = {
            'bom_ids': [],
            'ratio': [],
            'actual_price': [],
            'total_actual_price_temp': 0,
            'services': [],  # additional key for bom xn
            'standard_price': [],  # additional key for bom xn
            'ratio_standard_price': [],  # additional key for bom xn
            'total_standard_price': [],  # additional key for bom xn
        }
        if phieu and len(services) > 0:
            bom_id_array = []
            # find booking
            booking = phieu.booking_id
            if booking:
                crm_lines = booking.crm_line_ids.read_group(domain=[('crm_id', '=', booking.id)],
                                                    fields=['service_id', 'total'],
                                                    groupby=['service_id'])
                service_price = 0
                lab_bom_index = 0
                for service in services:
                    if type != 'LabTest':
                        boms = self.env['sh.medical.product.bundle'].search([('service_id', 'in', service.ids),
                                                                            ('region', '=', phieu.region),
                                                                            ('type', '=', type)])
                        common_bom = list(set(phieu.other_bom.ids) & set(boms.ids))
                        if boms and common_bom:
                            for bom in common_bom:
                                for crm_line in crm_lines:
                                    if crm_line['service_id'] and crm_line['service_id'][0] == service.id:
                                        bom_id_array.append(bom)
                                        service_price_ratio['bom_ids'].append(bom)
                                        service_price_ratio['ratio'].append(crm_line['total'])
                                        service_price_ratio['actual_price'].append(crm_line['total'])
                                        service_price_ratio['total_actual_price_temp'] += crm_line['total']
                    else:
                        for crm_line in crm_lines:
                            if crm_line['service_id'] and crm_line['service_id'][0] == service.id:
                                service_price += crm_line['total']
                                total_standard_price = 0
                                start_lab_bom_index = lab_bom_index
                                for lab_test_bom in phieu.other_bom:
                                    # for test
                                    # lab_test_bom.standard_cost = 200000

                                    bom_id_array.append(lab_test_bom.id)
                                    service_price_ratio['bom_ids'].append(lab_test_bom.id)
                                    service_price_ratio['ratio'].append(crm_line['total'])
                                    service_price_ratio['actual_price'].append(crm_line['total'])
                                    service_price_ratio['total_actual_price_temp'] = service_price

                                    service_price_ratio['services'].append(service.id)
                                    service_price_ratio['standard_price'].append(lab_test_bom.standard_cost)
                                    service_price_ratio['ratio_standard_price'].append(lab_test_bom.standard_cost)
                                    service_price_ratio['total_standard_price'].append(lab_test_bom.standard_cost)

                                    total_standard_price += lab_test_bom.standard_cost
                                    for i in range(lab_bom_index, start_lab_bom_index-1, -1):
                                        service_price_ratio['total_standard_price'][i] = total_standard_price
                                        service_price_ratio['ratio_standard_price'][i] = service_price_ratio['standard_price'][i] / total_standard_price if total_standard_price != 0 else 0

                                    lab_bom_index += 1

            bom_ids.append((6, 0, bom_id_array))
            index = 0
            for bom_id in service_price_ratio['bom_ids']:
                unit_price = self.env['stock.move'].get_done_unit_price_by_material_line(self._name, self.id) or 0.0

                # for test
                # unit_price = 20000
                if type != 'LabTest':
                    ratio = (service_price_ratio['ratio'][index]) / service_price_ratio['total_actual_price_temp'] if service_price_ratio['total_actual_price_temp'] != 0 else 0
                    service_price_ratio['ratio'][index] = ratio
                    service_price_ratio['actual_price'][index] = ratio * unit_price * quantity
                else:
                    service_ratio = (service_price_ratio['ratio'][index]) / service_price_ratio['total_actual_price_temp'] if service_price_ratio['total_actual_price_temp'] != 0 else 0
                    bom_ratio = service_price_ratio['ratio_standard_price'][index]
                    service_price_ratio['ratio'][index] = bom_ratio
                    service_price_ratio['actual_price'][index] = unit_price * service_ratio * quantity

                index += 1

        return bom_ids, json.dumps(service_price_ratio)


