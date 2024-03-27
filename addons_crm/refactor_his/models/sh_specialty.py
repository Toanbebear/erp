import datetime
from odoo.addons.queue_job.job import job
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.tools.profiler import profile

class QueueSpecialty(models.Model):
    _inherit = "sh.medical.specialty"

    def action_specialty_end(self):
        self.ensure_one()
        services_end_date = self.services_end_date if self.services_end_date else datetime.datetime.now()
        if self.state == 'Done':
            raise ValidationError('Phiếu đã được hoàn thành. Vui lòng F5 và kiểm tra lại.')
        if len(self.other_bom) != len(self.services):
            raise ValidationError('Số lượng BOM phải bằng số lượng dịch vụ.')
        if not self.supplies:
            raise ValidationError('Bạn phải nhập VTTH cho phiếu trước khi xác nhận hoàn thành!')
        if services_end_date > datetime.datetime.now():
            raise ValidationError('Bạn không thể đóng phiếu do Ngày giờ kết thúc lớn hơn ngày giờ hiện tại!')
        if not self.specialty_team:
            raise ValidationError('Bạn cần nhập Thành viên tham gia trước khi xác nhận hoàn thành')

        # tru vat tu theo tieu hao của phiếu khám chuyên khoa
        dept = self.department

        # 20220320 - tungnt - onnet
        default_production_location = self.env['stock.location'].get_default_production_location_per_company()

        vals = {}
        validate_str = ''

        for mat in self.supplies:
            if mat.qty_used > 0:  # CHECK SO LUONG SU DUNG > 0
                quantity_on_hand = self.env['stock.quant']._get_available_quantity(mat.supply.product_id,
                                                                                   mat.location_id)  # check quantity trong location
                if mat.uom_id != mat.supply.uom_id:
                    mat.write({'qty_used': mat.uom_id._compute_quantity(mat.qty_used, mat.supply.uom_id),
                               'uom_id': mat.supply.uom_id.id})  # quy so suong su dung ve don vi chinh cua san pham

                if quantity_on_hand < mat.qty_used:
                    validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
                        mat.supply.default_code, mat.supply.name, str(quantity_on_hand), str(mat.uom_id.name),
                        mat.location_id.name)

                else:  # truong one2many trong stock picking de tru cac product trong inventory
                    sub_vals = {
                        'name': 'THBN: ' + mat.supply.product_id.name,
                        'origin': str(self.sudo().walkin.id) + "-" + str(self.services.ids),  # mã pk-mã dịch vụ
                        'date': services_end_date,
                        'company_id': self.env.company.id,
                        'date_expected': services_end_date,
                        # 'date_done': services_end_date,
                        'product_id': mat.supply.product_id.id,
                        'product_uom_qty': mat.qty_used,
                        'product_uom': mat.uom_id.id,
                        'location_id': mat.location_id.id,
                        'location_dest_id': default_production_location.id,
                        'partner_id': self.patient.partner_id.id,
                        # xuat cho khach hang/benh nhan nao
                        'material_line_object': mat._name,
                        'material_line_object_id': mat.id,
                    }
                    if not vals.get(str(mat.location_id.id)):
                        vals[str(mat.location_id.id)] = [sub_vals]
                    else:
                        vals[str(mat.location_id.id)].append(sub_vals)

        # neu co vat tu tieu hao
        if vals and validate_str == '':
            # tao phieu xuat kho
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
                                                                  ('warehouse_id', '=',
                                                                   self.institution.warehouse_ids[0].id)],
                                                                 limit=1).id

            for location_key in vals:
                pick_note = 'THBN - %s - %s - %s' % (self.name, self.sudo().walkin.name, location_key)
                pick_vals = {'note': pick_note,
                             'origin': pick_note,
                             'partner_id': self.patient.partner_id.id,
                             'patient_id': self.patient.id,
                             'picking_type_id': picking_type,
                             'location_id': int(location_key),
                             'location_dest_id': default_production_location.id,
                             'date_done': services_end_date,
                             # xuat cho khach hang/benh nhan nao
                             # 'immediate_transfer': True,  # sẽ gây lỗi khi dùng lô, pick với immediate_transfer sẽ ko cho tạo move, chỉ tạo move line
                             # 'move_ids_without_package': vals[location_key]
                             }
                fail_pick_name = self.env['stock.picking'].search(
                    [('origin', 'ilike', 'THBN - %s - %s - %s' % (self.name, self.sudo().walkin.name, location_key))],
                    limit=1).name
                if fail_pick_name:
                    pick_vals['name'] = fail_pick_name.split('-', 1)[0]
                stock_picking = self.env['stock.picking'].create(pick_vals)
                for move_val in vals[location_key]:
                    move_val['name'] = stock_picking.name + " - " + move_val['name']
                    move_val['picking_id'] = stock_picking.id
                    self.env['stock.move'].create(move_val)
                stock_picking.with_context(exact_location=True).action_assign()
                self.sudo().with_delay(priority=0, channel='validate_picking_specialty').action_validate_picking(
                    picking_id=stock_picking.id, specialty_id=self.id, type='out')
                # TU DONG XÁC NHẬN XUAT KHO
                # stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
                # for move_line in stock_picking.move_ids_without_package:
                #     for move_live_detail in move_line.move_line_ids:
                #         move_live_detail.qty_done = move_live_detail.product_uom_qty
                #     # move_line.quantity_done = move_line.product_uom_qty
                # stock_picking.with_context(
                #     force_period_date=services_end_date).sudo().button_validate()  # ham tru product trong inventory, sudo để đọc stock.valuation.layer

                # sua ngay hoan thanh
                for move_line in stock_picking.move_ids_without_package:
                    move_line.move_line_ids.write({'date': services_end_date})  # sửa ngày hoàn thành ở stock move line
                stock_picking.move_ids_without_package.write(
                    {'date': services_end_date})  # sửa ngày hoàn thành ở stock move
                stock_picking.date_done = services_end_date
                stock_picking.sci_date_done = services_end_date

                stock_picking.create_date = self.services_date

                # Cập nhật ngược lại picking_id vào mats để truyền số liệu sang vật tư phiếu khám
                self.supplies.filtered(lambda s: s.location_id.id == int(location_key)).write(
                    {'picking_id': stock_picking.id})

        elif validate_str != '':
            raise ValidationError(
                _("Các loại Thuốc và Vật tư sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))

        res = self.write({'state': 'Done', 'services_end_date': services_end_date})

        # cap nhat vat tu cho phieu kham
        self.sudo().walkin.update_walkin_material(mats_types=['Specialty'])
        # Gửi message thông báo
        self.env['bus.bus'].sendone(
            (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
            {'type': 'simple_notification',
             'title': "Thông báo",
             'message': 'Đã đóng phiếu %s và đang tiến hành xuất VTTH.\nHệ thống sẽ thông báo lại nếu phát sinh lỗi xuất kho.' % self.name,
             'sticky': True,
             'warning': False})

    def reverse_materials(self):
        num_of_location = len(self.supplies.mapped('location_id'))
        pick_need_reverses = self.env['stock.picking'].search(
            [('origin', 'ilike', 'THBN - %s - %s' % (self.name, self.walkin.name)),
             ('company_id', '=', self.env.company.id)], order='create_date DESC', limit=num_of_location)
        if pick_need_reverses:
            for pick_need_reverse in pick_need_reverses:
                date_done = pick_need_reverse.date_done
                fail_pick_count = self.env['stock.picking'].search_count(
                    [('name', 'ilike', pick_need_reverse.name), ('company_id', '=', self.env.company.id)])
                pick_need_reverse.name += '-FP%s' % fail_pick_count
                pick_need_reverse.move_ids_without_package.write(
                    {'reference': pick_need_reverse.name})  # sửa cả trường tham chiếu của move.line (Dịch chuyển kho)

                new_wizard = self.env['stock.return.picking'].new(
                    {'picking_id': pick_need_reverse.id})  # tạo new wizard chưa lưu vào db
                new_wizard._onchange_picking_id()  # chạy hàm onchange với tham số ở trên
                wizard_vals = new_wizard._convert_to_write(
                    new_wizard._cache)  # lấy dữ liệu sau khi đã chạy qua onchange
                wizard = self.env['stock.return.picking'].with_context(reopen_flag=True, no_check_quant=True).create(
                    wizard_vals)
                new_picking_id, pick_type_id = wizard._create_returns()
                new_picking = self.env['stock.picking'].browse(new_picking_id)
                new_picking.with_context(exact_location=True).action_assign()
                self.sudo().with_delay(priority=0, channel='validate_picking_specialty').action_validate_picking(
                    picking_id=new_picking.id, specialty_id=self.id, type='in')

                # sua ngay hoan thanh
                for move_line in new_picking.move_ids_without_package:
                    move_line.move_line_ids.write(
                        {'date': date_done})  # sửa ngày hoàn thành ở stock move line
                new_picking.move_ids_without_package.write(
                    {'date': date_done})  # sửa ngày hoàn thành ở stock move

                new_picking.date_done = date_done
                new_picking.sci_date_done = date_done

    @job
    def action_validate_picking(self, picking_id, specialty_id, type):
        stock_picking = self.env['stock.picking'].sudo().browse(int(picking_id))
        specialty_id = self.env['sh.medical.specialty'].sudo().browse(int(specialty_id))
        # stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
        for move_line in stock_picking.move_ids_without_package:
            for move_live_detail in move_line.move_line_ids:
                move_live_detail.qty_done = move_live_detail.product_uom_qty
            # move_line.quantity_done = move_line.product_uom_qty
        stock_picking.with_context(
            force_period_date=specialty_id.services_end_date).sudo().button_validate()  # ham tru product trong inventory, sudo để đọc stock.valuation.layer
        if stock_picking.state != 'done':
            # Gửi message cảnh báo
            if type == 'out':
                message = "Lỗi xuất kho: Phiếu %s có mã phiếu điều chuyển kho %s.\nVui lòng báo lại bộ phận IT." % (
                specialty_id.name, stock_picking.name)
            else:
                message = "Lỗi nhập trả lại kho: Phiếu %s có mã phiếu điều chuyển kho %s.\nVui lòng báo lại bộ phận IT." % (
                    specialty_id.name, stock_picking.name)
            self.env['bus.bus'].sendone(
                (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
                {'type': 'simple_notification',
                 'title': "Thông báo",
                 'message': message,
                 'sticky': True,
                 'warning': False})
        # if stock_picking.state == 'done':
        #     message = "Phiếu %s có mã phiếu xuất kho %s thành công" % (specialty_id.name, stock_picking.name)
        #     hainn = self.env['res.users'].browse(6319).partner_id
        #     self.env['bus.bus'].sendone(
        #         [(self._cr.dbname, 'res.partner', self.env.user.partner_id.id)],
        #         {'type': 'simple_notification',
        #          'title': "Thông báo",
        #          'message': message,
        #          'sticky': True,
        #          'warning': False})