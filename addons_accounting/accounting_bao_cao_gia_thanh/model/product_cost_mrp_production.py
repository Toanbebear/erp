from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .constant import MRP_PRODUCTION_STATE
from .constant import MRP_PRODUCTION_STATE
import json


class ProductCostMrpProduction(models.AbstractModel):
    _name = 'product.cost.mrp.production'
    _description = 'mrp production'

    total_other_cost = fields.Float('Other cost')
    total_material_amount = fields.Float('Total material amount')
    total_other_amount = fields.Float('Total other amount')
    account_632 = fields.Many2one('account.account', string='Tk 632')


    def get_close_walking_date(self):
        return self.walkin.close_walkin

    def create_account_move(self, cost_line):
        move_ids = self.env['account.move'].sudo().create({
            'ref': cost_line.mrp_production_id.name + ' - ' + cost_line.mrp_production_id.product_id.name,
            'line_ids': [
                (0, 0, {
                    'account_id': cost_line.cost_driver_id.debit_account_id.id,
                    'debit': cost_line.planned_cost_of_activity,
                    'name': cost_line.mrp_production_id.name + ' - ' + cost_line.cost_driver_id.name,
                }),
                (0, 0, {
                    'account_id': cost_line.cost_driver_id.credit_account_id.id,
                    'credit': cost_line.planned_cost_of_activity,
                    'name': cost_line.mrp_production_id.name + ' - ' + cost_line.cost_driver_id.name,
                }),
            ]
        })
        move_ids.action_post()

    def button_mark_done(self):
        for order in self:
            total_other_cost = 0
            for cost_line in order.production_cost_line_ids:
                # self.create_account_move(cost_line)
                if cost_line.actual_count == 0 or cost_line.actual_cost_per_uom_unit == 0:
                    raise ValidationError('Please input actual count')
                else:
                    total_other_cost += cost_line.actual_cost_of_activity
            self.total_other_cost = total_other_cost
        res = super(ProductCostMrpProduction, self).button_mark_done()
        return res

    def compute_cost_line(self):
        if self.other_bom:
            production_cost_line_ids = [(5, 0, 0)]
            if self._name == 'sh.medical.lab.test':
                supplier_ratio = self.compute_supplies_ratio_by_bom(self.lab_test_material_ids)
            elif self._name == 'sh.medical.patient.rounding':
                supplier_ratio = self.compute_supplies_ratio_by_bom(self.medicaments)
            elif self._name == 'sh.medical.prescription':
                supplier_ratio = self.compute_supplies_ratio_by_bom(self.prescription_line)
            else:
                supplier_ratio = self.compute_supplies_ratio_by_bom(self.supplies)
            for his_bom in self.other_bom:
                for cost_driver in his_bom.cost_driver_ids:
                    if cost_driver.sci_company_id.id == self.walkin.institution.his_company.id:
                        if self._name == 'sh.medical.surgery':
                            perform_room = self.operating_room
                        elif self._name == 'sh.medical.patient.rounding':
                            perform_room = self.env['sh.medical.health.center.ot'].search([('code', '=', 'K_HN_1TC_HP')])
                        elif self._name == 'sh.medical.prescription':
                            perform_room = self.room_request
                        else:
                            perform_room = self.perform_room

                        if cost_driver.cost_driver_id.work_center_id == perform_room.work_center_id:
                            planned_cost_per_bom_unit = cost_driver.planned_cost_per_unit * cost_driver.planned_count
                            quantity = 1
                            # if self._name == 'sh.medical.lab.test' \
                            #         or self._name == 'sh.medical.surgery' \
                            #         or self._name == 'sh.medical.patient.rounding' \
                            #         or self._name == 'sh.medical.prescription':
                            #     quantity = 1
                            # else:
                            #     quantity = self.uom_price

                            cost_line_value = {
                                'cost_driver_id': cost_driver.cost_driver_id.id,
                                'uom_id': cost_driver.uom_id.id,
                                'planned_count': cost_driver.planned_count,
                                'planned_cost_per_uom_unit': cost_driver.planned_cost_per_unit,
                                'planned_cost_per_bom_unit': planned_cost_per_bom_unit,
                                'planned_cost_of_activity': planned_cost_per_bom_unit * quantity,
                                'actual_count': cost_driver.planned_count,
                                'complete_percentage': cost_driver.complete_percentage,
                                'work_center_id': cost_driver.cost_driver_id.work_center_id,
                                'service_id': his_bom.service_id.id if 'service_id' in his_bom else False,
                                'bom_id': his_bom.id,
                                'bom_object': his_bom._name,
                                'bom_cost_driver_id': cost_driver.id
                            }

                            if cost_driver.cost_driver_id.computation == 'equal_plan':
                                cost_line_value['actual_count'] = cost_driver.planned_count
                                cost_line_value['actual_cost_per_uom_unit'] = cost_driver.planned_cost_per_unit
                            elif cost_driver.cost_driver_id.computation == 'manual':
                                cost_line_value['actual_count'] = 0
                                cost_line_value['actual_cost_per_uom_unit'] = cost_driver.planned_cost_per_unit
                            elif cost_driver.cost_driver_id.computation == 'last_computed':
                                cost_line_value['actual_count'] = cost_driver.actual_count
                                cost_line_value['actual_cost_per_uom_unit'] = cost_driver.actual_cost_per_unit
                            elif cost_driver.cost_driver_id.computation == 'base_on_some_last_mo':
                                number_of_mo = 10
                                last_mrp_productions = self.env['sh.medical.specialty'].search(
                                    [('product_id', '=', self.product_id.id), ('state', '=', MRP_PRODUCTION_STATE['Done'])],
                                    limit=number_of_mo, order='date_planned_start desc')
                                total_actual_count = 0
                                total_actual_cost_per_uom_unit = 0
                                for last_mo in last_mrp_productions:
                                    for last_cost_line in last_mo.production_cost_line_ids:
                                        if last_cost_line.cost_driver_id.id == cost_driver.cost_driver_id.id:
                                            total_actual_count += last_cost_line.actual_count
                                            total_actual_cost_per_uom_unit += last_cost_line.actual_cost_per_uom_unit
                                cost_line_value['actual_count'] = total_actual_count / number_of_mo
                                cost_line_value['actual_cost_per_uom_unit'] = total_actual_cost_per_uom_unit / number_of_mo

                            if cost_driver.cost_driver_id.code == 'nvl':
                                nvl_actual_count = 1
                                cost_line_value['actual_count'] = nvl_actual_count
                                cost_line_value['actual_cost_per_uom_unit'] = 0

                                if self._name != 'sh.medical.lab.test':
                                    for supplier_ratio_item in supplier_ratio:
                                        index = 0
                                        for supplier_ratio_item_bom in supplier_ratio[supplier_ratio_item]['bom_ids']:
                                            if supplier_ratio_item_bom == his_bom.id:
                                                cost_line_value['actual_cost_per_uom_unit'] += supplier_ratio[supplier_ratio_item]['actual_price'][index]
                                            index += 1
                                else:
                                    # group by bom
                                    bom_services = {}
                                    for supplier_ratio_item in supplier_ratio:
                                        index = 0
                                        for supplier_ratio_item_bom in supplier_ratio[supplier_ratio_item]['bom_ids']:
                                            if supplier_ratio_item_bom == his_bom.id:

                                                bom_services.setdefault(
                                                    supplier_ratio[supplier_ratio_item]['services'][index],
                                                    {
                                                        "actual_cost_per_uom_unit": 0,
                                                        "actual_count": supplier_ratio[supplier_ratio_item]['ratio'][index]
                                                    },
                                                )["actual_cost_per_uom_unit"] += supplier_ratio[supplier_ratio_item]['actual_price'][index]

                                            index += 1

                                    for bom_service in bom_services:
                                        new_cost_line_value = cost_line_value.copy()
                                        new_cost_line_value['actual_cost_per_uom_unit'] = bom_services[bom_service]['actual_cost_per_uom_unit']
                                        new_cost_line_value['service_id'] = bom_service
                                        new_cost_line_value['actual_count'] = bom_services[bom_service]['actual_count']
                                        production_cost_line_ids.append((0, 0, new_cost_line_value))

                            elif cost_driver.cost_driver_id.compute_actual_count_base_on_working_hour:
                                if self._name == 'sh.medical.lab.test':
                                    start_date = self.date_analysis
                                    end_date = self.date_done
                                elif self._name == 'sh.medical.surgery':
                                    start_date = self.surgery_date
                                    end_date = self.surgery_end_date
                                elif self._name == 'sh.medical.patient.rounding':
                                    start_date = self.evaluation_start_date
                                    end_date = self.evaluation_end_date
                                elif self._name == 'sh.medical.prescription':
                                    start_date = self.date
                                    end_date = self.date_out
                                else:
                                    start_date = self.services_date
                                    end_date = self.services_end_date
                                working_hour_actual_count = int(
                                    ((end_date - start_date).total_seconds()) / 60)
                                cost_line_value['actual_count'] = working_hour_actual_count

                            # phiếu xét nghiệm không có các cost driver khác ngoài nguyên vật liệu
                            if self._name != 'sh.medical.lab.test':
                                production_cost_line_ids.append((0, 0, cost_line_value))

            self.production_cost_line_ids.unlink()
            self.production_cost_line_ids = production_cost_line_ids


    complete_amount = fields.Float("Complete", compute='_compute_operation_quantity')
    scrap_amount = fields.Float("Scrap", compute='_compute_operation_quantity')
    wip_amount = fields.Float("Wip", compute='_compute_operation_quantity')

    def compute_supplies_ratio_by_bom(self, supplier):
        ratio = {}
        total_material_amount = 0
        for item in supplier:
            if self._name == 'sh.medical.lab.test':
                product_of_item = item.product_id
            elif self._name == 'sh.medical.patient.rounding':
                product_of_item = item.medicine
            elif self._name == 'sh.medical.prescription':
                product_of_item = item.name
            else:
                product_of_item = item.supply

            if self._name == 'sh.medical.lab.test':
                actual_qty = item.quantity
            elif self._name == 'sh.medical.patient.rounding' or self._name == 'sh.medical.prescription':
                actual_qty = item.qty
            else:
                actual_qty = item.qty_used


            is_material_exist = False
            if self._name != 'sh.medical.lab.test':
                for bom in item.bom_ids:
                    if self._name == 'sh.medical.lab.test':
                        products = bom.lab_bom_lines
                    else:
                        products = bom.products

                    for bom_item in products:
                        if self._name == 'sh.medical.lab.test':
                            product_of_bom = bom_item.supply_id
                        else:
                            product_of_bom = bom_item.product_id

                        # vật tư trong bom
                        if product_of_item.id == product_of_bom.id:
                            is_material_exist = True
                            if product_of_item.id not in ratio:

                                unit_price = self.env['stock.move'].get_done_unit_price_by_material_line(item._name, item.id)

                                ratio[product_of_item.id] = {
                                    'bom_ids': [bom.id],
                                    'origin_qty': [bom_item.quantity],
                                    'actual_qty': [actual_qty],
                                    'actual_price': [actual_qty * unit_price],
                                    'total_origin_qty': bom_item.quantity,
                                    'total_actual_qty': actual_qty,
                                    'total_actual_price': actual_qty * unit_price,
                                    'ratio': [1],
                                }
                            else:
                                ratio[product_of_item.id]['bom_ids'].append(bom.id)
                                ratio[product_of_item.id]['origin_qty'].append(bom_item.quantity)
                                ratio[product_of_item.id]['total_origin_qty'] += bom_item.quantity
                                ratio[product_of_item.id]['actual_qty'] = []
                                ratio[product_of_item.id]['ratio'] = []
                                ratio[product_of_item.id]['actual_price'] = []

                                for computed_qty in ratio[product_of_item.id]['origin_qty']:
                                    actual_ratio = computed_qty / ratio[product_of_item.id]['total_origin_qty']
                                    ratio[product_of_item.id]['ratio'].append(actual_ratio)
                                    ratio[product_of_item.id]['actual_qty'].append(
                                        ratio[product_of_item.id]['total_actual_qty'] * actual_ratio)
                                    ratio[product_of_item.id]['actual_price'].append(
                                        ratio[product_of_item.id]['total_actual_price'] * actual_ratio)

            # vât tư ngoài bom
            if not is_material_exist:
                ratio[product_of_item.id] = json.loads(item.service_price_ratio)

            # compute total_material_amount
            # unit_price = self.env['stock.move'].get_done_unit_price_by_material_line(item._name, item.id) or 0.0
            # total_material_amount += unit_price * actual_qty

        # self.total_material_amount = total_material_amount
        return ratio

    def _compute_operation_quantity(self):
        for record in self:
            # sci have not used yet
            # stock_picking = self.env['stock.picking'].search(
            #     [('state', '=', 'done'), ('origin', '=', record.name)])
            # stock_move_lines = self.env['stock.move.line'].search(
            #     [('state', '=', 'done'), ('picking_id', 'in', stock_picking.ids)])
            #
            # scrap = 0
            # complete = 0
            # for line in stock_move_lines:
            #     if line.move_id.scrapped:
            #         scrap += line.qty_done
            #     elif line.location_id.barcode == 'WH-POSTPRODUCTION' and line.location_dest_id.barcode == 'WH-STOCK':
            #         complete += line.qty_done

            # record.complete_amount = complete
            # record.scrap_amount = scrap
            # record.wip_amount = record.uom_price - (record.complete_amount + record.scrap_amount)
            record.complete_amount = 0
            record.scrap_amount = 0
            record.wip_amount = 0

    def compute_material_n_other_amount(self):
        for record in self:
            total_material_amount = 0
            total_other_amount = 0
            for cost_line in record.production_cost_line_ids:
                if cost_line.cost_driver_id.code == 'nvl':
                    total_material_amount += cost_line.actual_cost_of_activity
                else:
                    total_other_amount += cost_line.actual_cost_of_activity
            record.total_material_amount = total_material_amount
            record.total_other_amount = total_other_amount

    step_1 = fields.Boolean()
    step_2 = fields.Boolean()
    step_3 = fields.Boolean()

    def get_ten_phieu(self):
        ma_phieu = ''
        if len(self.production_cost_line_ids) > 0:
            ma_phieu = self.production_cost_line_ids[0].ten_phieu
        return  ma_phieu

    def create_entry_credit_621_debit_154(self, journal, account_154, account_621):
        if self.total_material_amount > 0:
            step_1_move = self.env['account.move'].sudo().create({
                'type': 'entry',
                'date': self.get_close_walking_date(),
                'invoice_date': self.get_close_walking_date(),
                'journal_id': journal.id,
                'ref': self.get_ten_phieu(),
                'line_ids': [
                    (0, None, {
                        'name': 'Ket chuyen 621 sang 154 ERP',
                        'account_id': account_154.id,
                        'debit': abs(self.total_material_amount),
                        'credit': 0.0,
                    }),
                    (0, None, {
                        'name': 'Ket chuyen 621 sang 154 ERP',
                        'account_id': account_621.id,
                        'debit': 0.0,
                        'credit': abs(self.total_material_amount),
                    }),
                ]
            })
            step_1_move.post()
            if step_1_move.state == 'posted':
                return True
        else:
            return True
        return False

    def create_entry_credit_154_debit_632(self, journal, account_154, account_632, type):
        if type == 'nvl':
            value = abs(self.total_material_amount)
        else:
            value = abs(self.total_other_amount)

        if value > 0:
            move = self.env['account.move'].sudo().create({
                'type': 'entry',
                'date': self.get_close_walking_date(),
                'invoice_date': self.get_close_walking_date(),
                'journal_id': journal.id,
                'ref': self.get_ten_phieu(),
                'line_ids': [
                    (0, None, {
                        'name': 'Ghi nhận giá vốn ' + type,
                        'account_id': account_632.id,
                        'debit': value,
                        'credit': 0.0,
                    }),
                    (0, None, {
                        'name': 'Ghi nhận giá vốn ' + type,
                        'account_id': account_154.id,
                        'debit': 0.0,
                        'credit': value,
                    }),
                ]
            })
            move.post()
            if move.state == 'posted':
                return True
        else:
            return True
        return False

    def generate_journal_entry(self):
        for record in self:
            record.compute_material_n_other_amount()
            # get 154ERP account
            account_154 = self.env['account.account'].search([('is_154_erp', '=', True)], limit=1)
            if not account_154:
                raise ValidationError("Bạn chưa cấu hình tài khoản 154 ERP")
            # get 621 account
            production_location = self.env['stock.location'].get_default_production_location_per_company()
            if not production_location:
                raise ValidationError("Bạn chưa cấu hình kho sản xuất")
            if not production_location.account_621:
                raise ValidationError("Bạn chưa cấu hình tk 621 cho kho sản xuất")
            # get journal
            journal = self.env['account.journal'].search([('is_gia_thanh', '=', True)], limit=1)
            if not journal:
                raise ValidationError("Bạn chưa cấu hình sổ nhật ký giá thành")

            # get 632 account
            account_632 = False

            if hasattr(record, 'services'):
                for service in record.services:
                    if service.service_category and service.service_category.parent_id:
                        if service.service_category.parent_id.property_account_expense_categ_id:
                            account_632 = service.service_category.parent_id.property_account_expense_categ_id
                            break
            elif record._name == 'sh.medical.lab.test':  #lab test doesnt have field services
                for lab_test_material in record.lab_test_material_ids:
                    for service in lab_test_material.services:
                        if service.service_category and service.service_category.parent_id:
                            if service.service_category.parent_id.property_account_expense_categ_id:
                                account_632 = service.service_category.parent_id.property_account_expense_categ_id
                                break

            if not account_632:
                raise ValidationError("Bạn chưa cấu hình tk 632 cho nhóm dịch vụ")

            # region step 1: No 154, có 621
            if not record.step_1:
                record.step_1 = record.create_entry_credit_621_debit_154(journal, account_154, production_location.account_621)
            # endregion step 1

            # region step 2: No 632, có 154 cho nvl
            if record.step_1 and not record.step_2:
                record.step_2 = record.create_entry_credit_154_debit_632(journal, account_154, account_632, 'nvl')
            # endregion step 2

            # region step 3: No 632, có 154 cho cost driver khac
            if record.step_1 and record.step_2 and not record.step_3:
                record.step_3 = record.create_entry_credit_154_debit_632(journal, account_154, account_632, 'khác nvl')
            # endregion step 2

    def auto_compute_cost_line(self):
        self.ensure_one()
        if not self.production_cost_line_ids:
            self.sudo().compute_cost_line()

        if len(self.production_cost_line_ids) > 0:
            self.generate_journal_entry()

    def recompute_info(self):
        for record in self:
            for rec in record.production_cost_line_ids:
                rec._compute_ten_phieu()


class TasMrpBomCostDriver(models.Model):
    _name = "tas.mrp.production.cost.line"
    _description = "Mrp BOM production cost line "

    mrp_production_id = fields.Many2one('sh.medical.specialty', string="Phiếu chuyên khoa")
    mrp_production_lab_test_id = fields.Many2one('sh.medical.lab.test', string="Phiếu xét nghiệm")
    mrp_production_surgery_id = fields.Many2one('sh.medical.surgery', string="Phẫu thuật thủ thuật")
    mrp_production_patient_id = fields.Many2one('sh.medical.patient.rounding', string="Bệnh nhân lưu")
    mrp_production_prescription_id = fields.Many2one('sh.medical.prescription', string="Đơn thuốc")
    cost_driver_ratio = fields.Float(string="Cost driver ratio", default=1, compute='_compute_ten_phieu', compute_sudo=False, store=True)

    product_cost_report_id = fields.Many2one('tas.product.cost.report', string="Report")
    date_planned_start = fields.Datetime('Scheduled Date', default=lambda self: fields.Datetime.now())
    state = fields.Selection([
        ('Draft', _('Draft')),
        ('Confirmed', _('Confirmed')),
        ('In Progress', _('In Progress')),
        ('Done', _('Done')),
    ], string='State', default='Draft', compute='_compute_state', store=True)
    cost_driver_id = fields.Many2one('tas.cost.driver', string="Cost driver", required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='cost_driver_id.uom_id')
    planned_count = fields.Float("Planned Count", group_operator='avg')
    planned_cost_per_uom_unit = fields.Float("Planned Cost Per UOM Unit", group_operator='avg')
    planned_cost_per_bom_unit = fields.Float("Planned Cost Per Bom Unit", group_operator='avg')
    planned_cost_of_activity = fields.Float("Planned Cost Of Activity", group_operator='avg')
    actual_count = fields.Float("Actual Count", default=0, group_operator='avg')
    actual_count_per_bom_unit = fields.Float("Actual Count Per Bom Unit", default=0, group_operator='avg')
    actual_cost_per_uom_unit = fields.Float("Estimated Actual Cost Per Unit", default=0, group_operator='avg')
    actual_cost_per_bom_unit = fields.Float("Estimated Actual Cost Per Bom Unit", compute="_compute_actual_cost", store=True, group_operator='avg')
    actual_cost_of_activity = fields.Float("Estimated Actual Cost Of Activity", compute="_compute_actual_cost", store=True, group_operator='avg')
    recomputed_actual_cost_per_uom_unit = fields.Float("Actual Cost Per Unit", default=0, group_operator='avg')
    recomputed_actual_cost_per_bom_unit = fields.Float("Actual Cost Per Bom Unit", group_operator='avg')
    recomputed_actual_cost_of_activity = fields.Float("Actual Cost Of Activity", group_operator='avg')
    complete_percentage = fields.Float("Tỷ lệ hoàn thành")
    work_center_id = fields.Char(string='Mã tính giá thành')
    service_id = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ')
    bom_id = fields.Integer(string='Bom ID')
    bom_object = fields.Char(string='Bom Object')
    bom_cost_driver_id = fields.Many2one('tas.mrp.bom.cost.driver', string='Bom Cost Driver')
    is_recompute = fields.Boolean(string='Đã tính lại', default=False)
    bom_name = fields.Char(string='Bom Name', compute='_compute_bom_name')
    month_number = fields.Char(string='Month', compute='_compute_month_number')
    service_category_id = fields.Many2one('sh.medical.health.center.service.category', string='Nhóm dịch vụ', related='service_id.service_category')
    ten_phieu = fields.Char(string='Phiếu', compute='_compute_ten_phieu', compute_sudo=False)
    loai_phieu = fields.Char(string='Loai Phiếu', compute='_compute_ten_phieu', compute_sudo=False)
    ten_phieu_kham = fields.Char(string='Phiếu khám', compute='_compute_ten_phieu', compute_sudo=False)
    booking = fields.Char(string='Booking', compute='_compute_ten_phieu', compute_sudo=False)
    sale_order = fields.Char(string='Đơn hàng', compute='_compute_ten_phieu', compute_sudo=False)
    partner_id = fields.Many2one('res.partner', string='Khách hàng', compute='_compute_ten_phieu', compute_sudo=False)
    sci_company_id = fields.Many2one('res.company', related='cost_driver_id.sci_company_id', string='Company', store=True)

    @api.depends('mrp_production_id', 'mrp_production_lab_test_id', 'mrp_production_surgery_id', 'mrp_production_patient_id', 'mrp_production_prescription_id')
    def _compute_ten_phieu(self):
        for record in self:
            ten_phieu = ''
            loai_phieu = ''
            ten_phieu_kham = ''
            booking = ''
            sale_order = ''
            partner = False
            cost_driver_ratio = 1
            numbers_of_service = 1
            date_planned_start = fields.Datetime.now()
            if record.mrp_production_id:
                ten_phieu = record.mrp_production_id.name
                loai_phieu = record.mrp_production_id._name
                partner = record.mrp_production_id.patient
                date_planned_start = record.mrp_production_id.create_date
                ten_phieu_kham = str(record.mrp_production_id.walkin.name if record.mrp_production_id.walkin.name else '')
                sale_order = str(
                    record.mrp_production_id.walkin.sale_order_id.name if record.mrp_production_id.walkin.sale_order_id and record.mrp_production_id.walkin.sale_order_id.name else '')

                booking = str(record.mrp_production_id.booking_id.name if record.mrp_production_id.booking_id else '')
            if record.mrp_production_lab_test_id:
                ten_phieu = record.mrp_production_lab_test_id.name
                loai_phieu = record.mrp_production_lab_test_id._name
                partner = record.mrp_production_lab_test_id.patient
                cost_driver_ratio = record.actual_count
                # if len(record.mrp_production_lab_test_id.lab_test_material_ids) > 0:
                #     services = len(record.mrp_production_lab_test_id.lab_test_material_ids[0].services)
                #     if services > 0:
                #         numbers_of_service = services
                ten_phieu_kham = str(
                    record.mrp_production_lab_test_id.walkin.name if record.mrp_production_lab_test_id.walkin.name else '')
                sale_order = str(
                    record.mrp_production_lab_test_id.walkin.sale_order_id.name if record.mrp_production_lab_test_id.walkin.sale_order_id and record.mrp_production_lab_test_id.walkin.sale_order_id.name else '')

                date_planned_start = record.mrp_production_lab_test_id.create_date
                booking = str(record.mrp_production_lab_test_id.booking_id.name if record.mrp_production_lab_test_id.booking_id else '')

            if record.mrp_production_surgery_id:
                ten_phieu = record.mrp_production_surgery_id.name
                loai_phieu = record.mrp_production_surgery_id._name
                partner = record.mrp_production_surgery_id.patient
                date_planned_start = record.mrp_production_surgery_id.create_date
                ten_phieu_kham = str(
                    record.mrp_production_surgery_id.walkin.name if record.mrp_production_surgery_id.walkin.name else '')
                sale_order = str(
                    record.mrp_production_surgery_id.walkin.sale_order_id.name if record.mrp_production_surgery_id.walkin.sale_order_id and record.mrp_production_surgery_id.walkin.sale_order_id.name else '')

                booking = str(
                    record.mrp_production_surgery_id.booking_id.name if record.mrp_production_surgery_id.booking_id else '')
            if record.mrp_production_patient_id:
                ten_phieu = record.mrp_production_patient_id.name
                loai_phieu = record.mrp_production_patient_id._name
                partner = record.mrp_production_patient_id.patient
                date_planned_start = record.mrp_production_patient_id.create_date
                ten_phieu_kham = str(
                    record.mrp_production_patient_id.walkin.name if record.mrp_production_patient_id.walkin.name else '')
                sale_order = str(
                    record.mrp_production_patient_id.walkin.sale_order_id.name if record.mrp_production_patient_id.walkin.sale_order_id and record.mrp_production_patient_id.walkin.sale_order_id.name else '')

                booking = str(
                    record.mrp_production_patient_id.booking_id.name if record.mrp_production_patient_id.booking_id else '')
            if record.mrp_production_prescription_id:
                ten_phieu = record.mrp_production_prescription_id.name
                loai_phieu = record.mrp_production_prescription_id._name
                partner = record.mrp_production_prescription_id.patient
                date_planned_start = record.mrp_production_prescription_id.create_date
                ten_phieu_kham = str(
                    record.mrp_production_prescription_id.walkin.name if record.mrp_production_prescription_id.walkin.name else '')
                sale_order = str(
                    record.mrp_production_prescription_id.walkin.sale_order_id.name if record.mrp_production_prescription_id.walkin.sale_order_id and record.mrp_production_prescription_id.walkin.sale_order_id.name else '')

                booking = str(record.mrp_production_prescription_id.booking_id.name if record.mrp_production_prescription_id.booking_id else '')
            record.ten_phieu = ten_phieu
            record.loai_phieu = loai_phieu
            record.partner_id = partner.partner_id.id if partner and partner.partner_id else False
            record.cost_driver_ratio = cost_driver_ratio
            record.date_planned_start = date_planned_start
            record.ten_phieu_kham = ten_phieu_kham
            record.sale_order = sale_order
            record.booking = booking

    @api.depends('date_planned_start')
    def _compute_month_number(self):
        for record in self:
            month = 0
            if record.date_planned_start:
                month = record.date_planned_start.month
            record.month_number = str(month)

    @api.depends('bom_object', 'bom_id')
    def _compute_bom_name(self):
        for record in self:
            bom_name = ''
            if record.bom_object and record.bom_id:
                bom_name = self.env[record.bom_object].browse(record.bom_id).name
            record.bom_name = bom_name

    @api.depends('actual_count', 'actual_cost_per_uom_unit')
    def _compute_actual_cost(self):
        for record in self:
            record.actual_cost_per_bom_unit = record.actual_count * record.actual_cost_per_uom_unit

            quantity = 1
            # if record.loai_phieu == 'sh.medical.lab.test' \
            #         or record.loai_phieu == 'sh.medical.surgery' \
            #         or record.loai_phieu == 'sh.medical.patient.rounding' \
            #         or record.loai_phieu == 'sh.medical.prescription':
            #     quantity = 1
            # else:
            #     quantity = record.mrp_production_id.uom_price

            record.actual_cost_of_activity = record.actual_cost_per_bom_unit * quantity

    @api.depends('mrp_production_id')
    def _compute_state(self):
        for record in self:
            state = 'Draft'
            if record.mrp_production_id:
                state = record.mrp_production_id.state
            record.state = state
