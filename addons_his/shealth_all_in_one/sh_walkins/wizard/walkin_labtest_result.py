# -*- coding: utf-8 -*-

import json
from lxml import etree
from odoo import api, fields, models
import datetime
from datetime import timedelta
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare, pycompat


class WalkinLabtestsResult(models.TransientModel):
    _name = 'walkin.labtest.result'
    _description = 'Walkin labtest result'

    def get_room_domain(self):
        current_institution = self.env['sh.medical.health.center'].search([('his_company', '=', self.env.companies.ids[0])], limit=1)
        lab_depts = self.env['sh.medical.health.center.ward'].search([('institution', '=', current_institution.id), ('type', '=', 'Laboratory')])
        return [('department', 'in', lab_depts.ids)]

    patient = fields.Many2one('sh.medical.patient', string='Bệnh nhân', help="Tên bệnh nhân", readonly=True)
    service = fields.Many2many('sh.medical.health.center.service', 'sh_walkin_labtest_result_service_rel', 'walkin_labtest_result_id', 'service_id',
                               readonly=True, string='Dịch vụ')
    pathologist = fields.Many2one('sh.medical.physician', 'Kỹ thuật viên', domain=lambda self: [('company_id', '=', self.env.companies.ids[0])])
    perform_room = fields.Many2one('sh.medical.health.center.ot', string='Phòng thực hiện', domain=lambda self: self.get_room_domain())
    date_exam = fields.Datetime('Ngày khám', readonly=True)
    date_requested = fields.Datetime('Ngày yêu cầu')
    date_analysis = fields.Datetime('Ngày phân tích')
    date_done = fields.Datetime('Ngày trả kết quả')

    other_bom = fields.Many2many('sh.medical.lab.bom', string='Bom vật tư')
    supplies = fields.Many2many('sh.medical.lab.test.material', string="Vật tư")
    supply_domain = fields.Many2many('sh.medical.medicines', string='Supply domain', compute='_get_supply_domain')

    def onchange(self, values, field_name, field_onchange):
        real_fields = self._fields.keys()
        virtual_fields = [key for key in values.keys() if key not in real_fields]
        for key in virtual_fields:
            values.pop(key)
            field_onchange.pop(key)
        return super(WalkinLabtestsResult, self).onchange(values, field_name, field_onchange)

    @api.onchange('other_bom')
    def _onchange_other_bom(self):
        self.supplies = False
        if self.other_bom:
            vals = []
            check_duplicate = []
            for record in self.other_bom:
                for record_line in record.lab_bom_lines:
                    location = self.perform_room.location_supply_stock
                    if record_line.supply_id.medicament_type == 'Medicine':
                        location = self.perform_room.location_medicine_stock
                    # product = record_line.supply_id.product_id  # product.product
                    # if location:
                        # available_qty = self.env['stock.quant']._get_available_quantity(product_id=product, location_id=location)
                        # if record_line.uom_id != product.uom_id:
                        #     available_qty = product.uom_id._compute_quantity(available_qty, record_line.uom_id)
                        # qty = min(record_line.quantity, available_qty)
                        # if qty > 0:
                    qty = record_line.quantity
                    mats_id = record_line.supply_id.id
                    if mats_id not in check_duplicate:
                        check_duplicate.append(mats_id)
                        vals.append((0, 0, {'product_id': mats_id,
                                            'init_quantity': qty,
                                            'quantity': qty,
                                            'uom_id': record_line.uom_id.id,
                                            'location_id': location.id,
                                            'services': [(6, 0, self.service.ids)]}))
                        # 'notes': record_line.note}))
                    else:
                        old_supply_index = check_duplicate.index(mats_id)
                        vals[old_supply_index][2]['services'].append((6, 0, self.service.ids))
                        vals[old_supply_index][2]['init_quantity'] += qty
                        vals[old_supply_index][2]['quantity'] += qty
                        # vals[old_supply_index][2]['quantity'] = min(qty + vals[old_supply_index][2]['quantity'], available_qty)

            self.supplies = vals

    @api.onchange('date_analysis')
    def onchange_date_analysis(self):
        if not isinstance(self.date_analysis, str) and self.date_analysis:
            self.date_requested = datetime.datetime.strptime(self.date_analysis.strftime("%Y-%m-%d %H:%M:%S"),
                                                             "%Y-%m-%d %H:%M:%S") - timedelta(
                minutes=10) or fields.Datetime.now()

    @api.depends('perform_room', 'supplies')
    def _get_supply_domain(self):
        for record in self:
            record.supply_domain = False
            room = record.perform_room
            if room:
                locations = room.location_medicine_stock + room.location_supply_stock
                if locations:
                    products = self.env['stock.quant'].search([('quantity', '>', 0), ('location_id', 'in', locations.ids)]).filtered(lambda q: q.reserved_quantity < q.quantity).mapped('product_id')
                    if products:
                        medicine_ids = self.env['sh.medical.medicines'].search([('product_id', 'in', products.ids)]).ids
                        to_exclude = [supply.product_id.id for supply in record.supplies if supply.product_id]
                        final_domain = [i for i in medicine_ids if i not in to_exclude]
                        record.supply_domain = [(6, 0, final_domain)]

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(WalkinLabtestsResult, self).fields_get(allfields, attributes=attributes)
        walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.env.context.get('active_id'))
        current_institution = self.env['sh.medical.health.center'].search([('his_company', '=', self.env.companies.ids[0])], limit=1)
        lab_tests = walkin.lab_test_ids.filtered(lambda l: l.state != 'Completed' and l.institution == current_institution)
        for lab_test in lab_tests:
            if not lab_test.lab_test_criteria:
                field_name = 'result_%s' % lab_test.id
                res[field_name] = {'type': 'char',
                                   'string': lab_test.test_type.name,
                                   'exportable': False,
                                   'selectable': False}
            else:
                for criteria in lab_test.lab_test_criteria:
                    c_field_name = 'result_%s_%s' % (lab_test.id, criteria.id)
                    res[c_field_name] = {'type': 'char',
                                         'string': criteria.name,
                                         'exportable': False,
                                         'selectable': False}
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        self.env['ir.actions.actions'].clear_caches()
        res = super(WalkinLabtestsResult, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_id == self.env.ref('shealth_all_in_one.walkin_labtest_result_view_form').id:
            doc = etree.XML(res['arch'])
            result_page = doc.find("./notebook/page[@name='result']")
            walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.env.context.get('active_id'))
            current_institution = self.env['sh.medical.health.center'].search([('his_company', '=', self.env.companies.ids[0])], limit=1)
            lab_tests = walkin.lab_test_ids.filtered(lambda l: l.state != 'Completed' and l.institution == current_institution)
            lab_groups = lab_tests.mapped('group_type')
            for group in lab_groups:
                xml_lab_group = etree.SubElement(result_page, 'group', {'col': '3', 'string': group.name, 'class': 'sh_result_labtest'})
                etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '<b>Loại Xét nghiệm</b>'
                etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '<b>Kết quả</b>'
                etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '<b>Khoảng bình Thường</b>'
                index = 1
                for lab_test in lab_tests.filtered(lambda t: t.group_type == group):
                    span1 = etree.SubElement(xml_lab_group, 'span')
                    b = etree.SubElement(span1, 'b', {'class': 'text-primary'})
                    b.text = '. '.join([str(index), lab_test.test_type.name])

                    index += 1

                    if not lab_test.lab_test_criteria:
                        field_name = 'result_%s' % lab_test.id
                        etree.SubElement(xml_lab_group, 'field', {'name': field_name, 'nolabel': '1'})
                        # etree.SubElement(xml_lab_group, 'field', {'name': field_name, 'nolabel': '1', 'required': '1'})
                        # for node in doc.xpath("//field[@name='%s']" % field_name):
                        #     node.set("required", "1")
                        #     node.set("modifiers", json.dumps({'required': True}))
                        etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '_'
                    else:
                        etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '_'
                        etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '_'
                        for criteria in lab_test.lab_test_criteria:
                            c_span1 = etree.SubElement(xml_lab_group, 'span', {'class': 'ml-3'})
                            c_span1.text = criteria.name
                            c_field_name = 'result_%s_%s' % (lab_test.id, criteria.id)
                            etree.SubElement(xml_lab_group, 'field', {'name': c_field_name, 'nolabel': '1'})
                            # etree.SubElement(xml_lab_group, 'field', {'name': c_field_name, 'nolabel': '1', 'required': '1'})
                            # for node in doc.xpath("//field[@name='%s']" % c_field_name):
                            #     node.set("required", "1")
                            #     node.set("modifiers", json.dumps({'required': True}))
                            c_span3 = etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'})
                            c_span3.text = ' '.join([criteria.normal_range or '', criteria.units.name or ''])
            footer = etree.SubElement(doc, 'footer')
            etree.SubElement(footer, 'button', {'string': 'Trả kết quả', 'name': 'action_apply', 'type': 'object', 'class': 'btn-primary'})
            etree.SubElement(footer, 'button', {'string': 'Hủy', 'special': 'cancel', 'class': 'btn-secondary'})
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.model
    def create(self, vals):
        walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.env.context.get('active_id'))
        code_company_walkin = walkin.company_id.code
        config = self.env['ir.config_parameter'].sudo()
        code_companies = eval(config.get_param('list_company_connect_labconn'))
        # check cong ty ket noi may xet nghiem de khong ghi de KQ XN khi tra KQ XN
        if code_company_walkin in code_companies:
            current_institution = self.env['sh.medical.health.center'].search(
                [('his_company', '=', self.env.companies.ids[0])], limit=1)
            first_lab = True
            if not vals.get('supplies'):
                raise ValidationError('Trường vật tư không hợp lệ.')
            for lab_test in walkin.lab_test_ids.filtered(
                    lambda l: l.state != 'Completed' and l.institution == current_institution):
                lab_test.set_to_test_inprogress()
                test_vals = {'pathologist': vals.get('pathologist'),
                             'perform_room': vals.get('perform_room'),
                             'date_analysis': vals.get('date_analysis'),
                             'date_done': vals.get('date_done'),
                             'date_requested': vals.get('date_requested')}
                # if not lab_test.lab_test_criteria:
                #     # test_vals['results'] = vals.get('result_%s' % lab_test.id)
                #     test_vals['results'] = vals.get('result_%s' % lab_test.id) or 'KQ'
                # else:
                #     for criteria in lab_test.lab_test_criteria:
                #         # criteria.result = vals.get('result_%s_%s' % (lab_test.id, criteria.id))
                #         criteria.result = vals.get('result_%s_%s' % (lab_test.id, criteria.id)) or 'KQ'
                if first_lab:
                    test_vals['lab_test_material_ids'] = vals.get('supplies')
                    first_lab = False
                lab_test.write(test_vals)
                lab_test.with_context(ignore_expired=lab_test.date_analysis).set_to_test_complete()
            return super(WalkinLabtestsResult, self).create({})
        else:
            current_institution = self.env['sh.medical.health.center'].search(
                [('his_company', '=', self.env.companies.ids[0])], limit=1)
            first_lab = True
            if not vals.get('supplies'):
                raise ValidationError('Trường vật tư không hợp lệ.')
            for lab_test in walkin.lab_test_ids.filtered(
                    lambda l: l.state != 'Completed' and l.institution == current_institution):
                lab_test.set_to_test_inprogress()
                test_vals = {'pathologist': vals.get('pathologist'),
                             'perform_room': vals.get('perform_room'),
                             'date_analysis': vals.get('date_analysis'),
                             'date_done': vals.get('date_done'),
                             'date_requested': vals.get('date_requested')}
                if not lab_test.lab_test_criteria:
                    test_vals['results'] = vals.get('result_%s' % lab_test.id) or 'KQ'
                else:
                    for criteria in lab_test.lab_test_criteria:
                        criteria.result = vals.get('result_%s_%s' % (lab_test.id, criteria.id)) or 'KQ'
                if first_lab:
                    test_vals['lab_test_material_ids'] = vals.get('supplies')
                    first_lab = False
                lab_test.write(test_vals)
                lab_test.with_context(ignore_expired=lab_test.date_analysis).set_to_test_complete()
            return super(WalkinLabtestsResult, self).create({})

    def read(self, fields, load='_classic_read'):
        real_fields = self._fields.keys()
        filtered_fields = [field for field in fields if field in real_fields]
        return super(WalkinLabtestsResult, self).read(filtered_fields, load)

    def action_apply(self):
        return {'type': 'ir.actions.act_window_close'}

    # @api.model
    # def fields_view_get_backup(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     self.env['ir.actions.actions'].clear_caches()
    #     res = super(WalkinLabtestsResult, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_id == self.env.ref('shealth_all_in_one.walkin_labtest_result_view_form').id:
    #         doc = etree.XML(res['arch'])
    #         all_fields = {}
    #         walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.env.context.get('active_id'))
    #         lab_tests = walkin.lab_test_ids.filtered(lambda l: l.state != 'Completed')
    #         lab_groups = lab_tests.mapped('group_type')
    #         for group in lab_groups:
    #             etree.SubElement(doc, 'separator', {'string': group.name})
    #             xml_lab_group = etree.SubElement(doc, 'group', {'col': '3'})
    #             etree.SubElement(xml_lab_group, 'span').text = '<b>Xét nghiệm</b>'
    #             etree.SubElement(xml_lab_group, 'span').text = '<b>Kết quả</b>'
    #             etree.SubElement(xml_lab_group, 'span').text = '<b>Khoảng bình Thường</b>'
    #             for lab_test in lab_tests.filtered(lambda t: t.group_type == group):
    #                 test_group = etree.SubElement(doc, 'group', {'col': '3'})
    #                 span1 = etree.SubElement(test_group, 'span')
    #                 b = etree.SubElement(span1, 'i')
    #                 b.text = lab_test.test_type.name
    #                 if not lab_test.lab_test_criteria:
    #                     field_name = 'result_%s' % lab_test.id
    #                     etree.SubElement(test_group, 'field', {'name': field_name, 'nolabel': '1', 'required': '1'})
    #                     for node in doc.xpath("//field[@name='%s']" % field_name):
    #                         node.set("required", "1")
    #                         node.set("modifiers", json.dumps({'required': True}))
    #                     all_fields[field_name] = {'type': 'text',
    #                                               'string': 'Result',
    #                                               'exportable': False,
    #                                               'selectable': False}
    #                     etree.SubElement(test_group, 'span').text = '_'
    #                 else:
    #                     etree.SubElement(test_group, 'span').text = '_'
    #                     etree.SubElement(test_group, 'span').text = '_'
    #                     for criteria in lab_test.lab_test_criteria:
    #                         c_group = etree.SubElement(doc, 'group', {'col': '3'})
    #                         c_span1 = etree.SubElement(c_group, 'span')
    #                         c_span1.text = criteria.name
    #                         c_field_name = 'result_%s_%s' % (lab_test.id, criteria.id)
    #                         etree.SubElement(c_group, 'field', {'name': c_field_name, 'nolabel': '1', 'required': '1'})
    #                         for node in doc.xpath("//field[@name='%s']" % c_field_name):
    #                             node.set("required", "1")
    #                             node.set("modifiers", json.dumps({'required': True}))
    #                         all_fields[c_field_name] = {'type': 'char',
    #                                                     'string': 'Result',
    #                                                     'exportable': False,
    #                                                     'selectable': False}
    #                         c_span3 = etree.SubElement(c_group, 'span')
    #                         c_span3.text = ' '.join([criteria.normal_range or '', criteria.units.name or ''])
    #         res['arch'] = etree.tostring(doc, encoding='unicode')
    #         res['fields'].update(all_fields)
    #         # print(res)
    #     return res
