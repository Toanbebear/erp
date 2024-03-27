import datetime
import logging
import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning

_logger = logging.getLogger(__name__)


# Imaging Test Type Management
class SHealthImagingGroupType(models.Model):
    _name = 'sh.medical.imaging.group.type'
    _description = 'Imaging Group Type Configuration'

    name = fields.Char(string='Name', size=128, required=True)
    info = fields.Text(string='Description')
    type = fields.Selection([('cdha', 'Chuẩn đoán hình ảnh'), ('tdcn', 'Thăm dò chức năng')], string='Loại')


class SHealthImagingTestType(models.Model):
    _name = 'sh.medical.imaging.test.type'
    _description = 'Imaging Test Type Configuration'

    _inherits = {
        'product.product': 'product_id',
    }

    product_id = fields.Many2one('product.product', string='Related Product', required=True, ondelete='cascade',
                                 help='Product-related data of the labtest types')

    # name = fields.Char(string='Name', size=128, required=True)
    # code = fields.Char(string='Code', size=25, required=True)
    # test_charge = fields.Float(string='Test Charge', required=True, default=lambda *a: 0.0)
    # imaging_department = fields.Many2one('sh.medical.imagingtest.department', string='Department')
    info = fields.Text(string='Thông tin')
    analysis = fields.Html(string='Phân tích mẫu')
    conclusion = fields.Text(string='Kết luận mẫu')
    # institution = fields.Many2one('sh.medical.health.center', string='Health Center', help="Medical Center")
    # department = fields.Many2one('sh.medical.health.center.ward', string='Department',
    #                              help="Department of the selected Health Center",
    #                              domain="[('institution','=',institution)]")
    # thong tin vat tu
    material_ids = fields.One2many('sh.medical.imaging.test.type.material', 'imaging_types_id',
                                   string="Material Information")

    perform_room = fields.Many2one('sh.medical.health.center.ot', string='Phòng thực hiện')

    # gruop_type
    group_type = fields.Many2one('sh.medical.imaging.group.type', string='Group',
                                 help="Group of the imaging test type")

    # _sql_constraints = [('name_uniq', 'unique(name)', 'The Imaging test type name must be unique')]


class SHealthImagingTestTypeMaterial(models.Model):
    _name = 'sh.medical.imaging.test.type.material'
    _description = 'All material of the Imaging Test Types'

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự
    imaging_types_id = fields.Many2one('sh.medical.imaging.test.type', string='Imaging Test Types')
    product_id = fields.Many2one('sh.medical.medicines', string='Product', required=True, domain=lambda self: [
        ('categ_id', 'child_of', self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    quantity = fields.Float('Quantity', digits='Product Unit of Measure')  # số lượng sử dụng vật tư
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')

    @api.onchange('product_id')
    def _change_product_id(self):
        self.uom_id = self.product_id.uom_id

        return {'domain': {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.product_id.uom_id.category_id:
            self.uom_id = self.product_id.uom_id
            raise Warning(
                _('The Imaging Test Types Unit of Measure and the Material Unit of Measure must be in the same category.'))


# Imaging Test Management

class SHealthImagingTypeManagement(models.Model):
    _name = 'sh.medical.imaging'
    _description = 'Imaging Test Management'

    _inherit = ['mail.thread']

    _order = "walkin"

    IMAGING_STATE = [
        ('Draft', 'Nháp'),
        ('Test In Progress', 'Đang thực hiện'),
        ('Completed', 'Hoàn thành'),
        # ('Cancelled', 'Cancelled'),
        # ('Invoiced', 'Invoiced'),
    ]

    name = fields.Char(string='Test #', size=16, required=True, readonly=True, default=lambda *a: '/')
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True,
                              states={'Draft': [('readonly', False)]})
    # imaging_department = fields.Many2one('sh.medical.imagingtest.department', string='Department', readonly=True, states={'Draft': [('readonly', False)]})
    test_type = fields.Many2one('sh.medical.imaging.test.type', string='Test Type', required=True, readonly=True,
                                states={'Draft': [('readonly', False)]}, help="Imaging Test type")
    pathologist = fields.Many2one('sh.medical.physician', string='Pathologist', help="Pathologist",
                                  readonly=False, states={'Completed': [('readonly', True)]})
    requestor = fields.Many2one('sh.medical.physician', string='Doctor who requested the test',
                                domain=[('is_pharmacist', '=', False)], help="Doctor who requested the test",
                                readonly=True, states={'Draft': [('readonly', False)]})
    analysis = fields.Html(string='Analysis', readonly=True, states={'Test In Progress': [('readonly', False)]})
    conclusion = fields.Text(string='Conclusion', readonly=True, states={'Test In Progress': [('readonly', False)]})
    date_requested = fields.Datetime(string='Date requested', readonly=True,
                                     states={'Draft': [('readonly', False)], 'Test In Progress': [('readonly', False)]},
                                     default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    date_analysis = fields.Datetime(string='Date of the Analysis', readonly=True,
                                    states={'Draft': [('readonly', False)], 'Test In Progress': [('readonly', False)]})
    date_done = fields.Datetime(string='Date of the return result', readonly=True,
                                states={'Draft': [('readonly', False)], 'Test In Progress': [('readonly', False)]})
    state = fields.Selection(IMAGING_STATE, string='State', readonly=True, default=lambda *a: 'Draft')
    image1 = fields.Binary(string="Image 1", readonly=True, states={'Test In Progress': [('readonly', False)]})
    image2 = fields.Binary(string="Image 2", readonly=True, states={'Test In Progress': [('readonly', False)]})
    image3 = fields.Binary(string="Image 3", readonly=True, states={'Test In Progress': [('readonly', False)]})
    image4 = fields.Binary(string="Image 4", readonly=True, states={'Test In Progress': [('readonly', False)]})
    image5 = fields.Binary(string="Image 5", readonly=True, states={'Test In Progress': [('readonly', False)]})
    image6 = fields.Binary(string="Image 6", readonly=True, states={'Test In Progress': [('readonly', False)]})

    institution = fields.Many2one('sh.medical.health.center', string='Health Center', help="Medical Center")
    department = fields.Many2one('sh.medical.health.center.ward', string='Khoa/Phòng',
                                 help="Department of the selected Health Center",
                                 domain="[('institution','=',institution),('type','=','Laboratory')]")
    # domain="[('institution','=',institution),('type','=','Imaging')]")

    perform_room = fields.Many2one('sh.medical.health.center.ot', string='Performance room',
                                   domain="[('department','=',department)]", readonly=True,
                                   states={'Draft': [('readonly', False)]})

    # thong tin vat tu
    imaging_material_ids = fields.One2many('sh.medical.imaging.material', 'imaging_id',
                                           string="Material Information")

    #  check công ty hiện tại của người dùng với công ty của phiếu
    check_current_company = fields.Boolean(string='Cty hiện tại', compute='_check_current_company')

    #  domain vật tư và thuốc theo kho của phòng
    supply_domain = fields.Many2many('sh.medical.medicines', string='Supply domain', compute='_get_supply_domain')

    doctor_note = fields.Text(string='Ghi chú', readonly=False,
                              states={'Completed': [('readonly', True)]})

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', readonly=True, ondelete='cascade')
    allow_institutions = fields.Many2many('sh.medical.health.center', string='Allow institutions', related='walkin.allow_institutions')

    # Áp dụng rule CDHA - share company
    company_id = fields.Many2one('res.company', related='walkin.company_id',
                                 string='Company',
                                 store=True,
                                 readonly=True,
                                 ondelete='cascade')
    company2_id = fields.Many2many('res.company', 'sh_medical_imaging_company_related_rel', 'imaging_id', 'company_id',
                                   related='walkin.company2_id',
                                   store=True,
                                   readonly=True,
                                   ondelete='cascade')

    @api.depends('institution.his_company')
    def _check_current_company(self):
        for record in self:
            record.check_current_company = True if record.institution.his_company == self.env.company else False

    @api.depends('perform_room')
    def _get_supply_domain(self):
        for record in self:
            record.supply_domain = False
            room = record.perform_room
            if room:
                locations = room.location_medicine_stock + room.location_supply_stock
                if locations:
                    products = self.env['stock.quant'].search(
                        [('quantity', '>', 0), ('location_id', 'in', locations.ids)]).filtered(
                        lambda q: q.reserved_quantity < q.quantity).mapped('product_id')
                    if products:
                        medicines = self.env['sh.medical.medicines'].search([('product_id', 'in', products.ids)])
                        record.supply_domain = [(6, 0, medicines.ids)]

    @api.onchange('date_requested', 'date_analysis', 'date_done')
    def _onchange_date_imaging(self):
        if self.date_analysis and self.date_requested and self.date_done:
            if self.date_analysis < self.date_requested or self.date_analysis > self.date_done:
                raise UserError(
                    _('Thông tin không hợp lệ! Ngày phân tích phải sau ngày yêu cầu và trước ngày trả kết quả!'))

    def write(self, vals):
        if vals.get('date_requested') or vals.get('date_analysis') or vals.get('date_done'):
            for record in self:
                date_requested = vals.get('date_requested') or record.date_requested
                date_analysis = vals.get('date_analysis') or record.date_analysis
                date_done = vals.get('date_done') or record.date_done

                # format to date
                if isinstance(date_requested, str):
                    date_requested = datetime.datetime.strptime(date_requested, '%Y-%m-%d %H:%M:%S')
                if isinstance(date_analysis, str):
                    date_analysis = datetime.datetime.strptime(date_analysis, '%Y-%m-%d %H:%M:%S')
                if isinstance(date_done, str):
                    date_done = datetime.datetime.strptime(date_done, '%Y-%m-%d %H:%M:%S')

            if date_analysis and date_requested and date_done and (
                    date_analysis < date_requested or date_analysis > date_done):
                raise UserError(
                    _('Thông tin không hợp lệ! Ngày phân tích phải sau ngày yêu cầu và trước ngày trả kết quả!'))

        return super(SHealthImagingTypeManagement, self).write(vals)

    @api.depends('test_type')
    def compute_test_type(self):
        for rec in self:
            rec.group_type = rec.test_type.group_type if rec.test_type else False

    # gruop_type
    group_type = fields.Many2one('sh.medical.imaging.group.type', string='Group', store="True",
                                 help="Group of the imaging test type", compute=compute_test_type)

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.imaging.%s' % vals['institution'])
        if not sequence:
            raise ValidationError(_('Định danh phiếu CHĐA của Cơ sở y tế này đang không tồn tại!'))
        vals['name'] = sequence
        _logger.info(vals['institution'])
        return super(SHealthImagingTypeManagement, self).create(vals)

    def print_patient_imaging(self):
        return self.env.ref('shealth_all_in_one.action_report_patient_imaging').report_action(self)

    def view_detail_imaging(self):
        return {
            'name': _('Chi tiết CĐHA'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_imaging_test_form').id,
            'res_model': 'sh.medical.imaging',  # model want to display
            'target': 'current',  # if you want popup,
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': self.id
        }

    # Preventing deletion of a imaging details which is not in draft state
    def unlink(self):
        for imaging in self.filtered(lambda imaging: imaging.state not in ['Draft']):
            raise UserError(_('You can not delete imaging information which is not in "Draft" state !!'))
        return super(SHealthImagingTypeManagement, self).unlink()

    def reverse_materials(self):
        key_words = 'THBN - %s - %s' % (self.name, self.walkin.name)
        pick_need_reverse = self.env['stock.picking'].search(
            [('origin', 'ilike', key_words), ('company_id', '=', self.env.company.id)], order='create_date DESC',
            limit=1)
        fail_pick_count = self.env['stock.picking'].search_count(
            [('name', 'ilike', pick_need_reverse.name), ('company_id', '=', self.env.company.id)])
        if pick_need_reverse.id:
            date_done = pick_need_reverse.date_done
            pick_need_reverse.name += '-FP%s' % fail_pick_count
            pick_need_reverse.move_ids_without_package.write(
                {'reference': pick_need_reverse.name})  # sửa cả trường tham chiếu của move.line (Dịch chuyển kho)

            new_wizard = self.env['stock.return.picking'].new(
                {'picking_id': pick_need_reverse.id})  # tạo new wizard chưa lưu vào db
            new_wizard._onchange_picking_id()  # chạy hàm onchange với tham số ở trên
            wizard_vals = new_wizard._convert_to_write(new_wizard._cache)  # lấy dữ liệu sau khi đã chạy qua onchange
            wizard = self.env['stock.return.picking'].with_context(reopen_flag=True, no_check_quant=True).create(
                wizard_vals)
            new_picking_id, pick_type_id = wizard._create_returns()
            new_picking = self.env['stock.picking'].browse(new_picking_id)
            new_picking.with_context(exact_location=True).action_assign()
            for move_line in new_picking.move_ids_without_package:
                for move_live_detail in move_line.move_line_ids:
                    move_live_detail.qty_done = move_live_detail.product_uom_qty
                # move_line.quantity_done = move_line.product_uom_qty
            new_picking.with_context(force_period_date=date_done).button_validate()

            # sua ngay hoan thanh
            for move_line in new_picking.move_ids_without_package:
                move_line.move_line_ids.write(
                    {'date': date_done})  # sửa ngày hoàn thành ở stock move line
            new_picking.move_ids_without_package.write(
                {'date': date_done})  # sửa ngày hoàn thành ở stock move

            new_picking.date_done = date_done
            new_picking.sci_date_done = date_done

    def set_to_test_start(self):
        if self.state == 'Completed':
            self.reverse_materials()
            self.walkin.update_walkin_material(mats_types=['Imaging'])
            res = self.write({'state': 'Test In Progress'})
        else:
            # self.imaging_material_ids = False
            # ghi nhận giá trị và vtth mẫu từ test type
            # if self.test_type:
            #     lt_data = []
            #     # test_type_id = self.test_type.id
            #     # test_type = self.env['sh.medical.imaging.test.type'].sudo().browse(test_type_id)
            #     seq = 0
            #     for lt in self.test_type.material_ids:
            #         seq += 1
            #         lt_data.append((0, 0, {'sequence': seq,
            #                                'product_id': lt.product_id.id,
            #                                'init_quantity': lt.quantity,
            #                                'is_init': True,
            #                                'uom_id': lt.uom_id.id}))
            # log access patient
            # data_log = self.env['sh.medical.patient.log'].search([('walkin', '=', self.walkin.id)])
            # data_cdha = False
            # for data in data_log:
            #     # nếu đã có data log cho khoa xn này rồi
            #     if data.department.id == self.department.id:
            #         data_cdha = data
            #     # nếu có log khoa KB rồi thì cập nhật ngày ra cho khoa kb là ngày bắt đầu làm dịch vụ
            #     if data.department.type == 'Examination':
            #         data.date_out = self.date_analysis if self.date_analysis else datetime.datetime.now()
            # # nếu chưa có data log=> tạo log
            # if not data_cdha:
            #     vals_log = {'walkin': self.walkin.id,
            #                 'patient': self.patient.id,
            #                 'department': self.department.id,
            #                 'date_in': self.date_analysis if self.date_analysis else datetime.datetime.now()}
            #     self.env['sh.medical.patient.log'].create(vals_log)
            # else:
            #     data_cdha.date_in = self.date_analysis if self.date_analysis else datetime.datetime.now()
            #     data_cdha.date_out = False

            res = self.write({'state': 'Test In Progress', 'analysis': self.test_type.analysis,
                              'conclusion': self.test_type.conclusion,
                              'date_analysis': self.date_analysis if self.date_analysis else datetime.datetime.now()})

        # update so pttt hoan thanh
        Walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.walkin.id)
        img_done = self.env['sh.medical.imaging'].search_count(
            [('walkin', '=', self.walkin.id), ('state', '=', 'Completed')])
        img_total = self.env['sh.medical.imaging'].search_count(
            [('walkin', '=', self.walkin.id), ('state', '!=', 'Cancelled')])
        Walkin.write({'img_test_done_count': img_done, 'has_img_result': True if img_total - img_done == 0 else False})

        # return res

    def set_to_test_draft(self):
        self.write({'state': 'Draft', 'date_analysis': False})

    def set_to_test_complete(self):
        self.ensure_one()
        if not self.analysis:
            raise UserError(_('Bạn không thể xác nhận phiếu hoàn thành khi chưa nhập chi tiết phân tích.'))
        if not self.conclusion:
            raise UserError(_('Bạn không thể xác nhận phiếu hoàn thành khi chưa nhập kết luận.'))

        dept = self.department
        room = self.perform_room
        if self.date_done:
            date_done = self.date_done
        else:
            date_done = fields.Datetime.now()

        vals = []
        validate_str = ''
        for mat in self.imaging_material_ids:
            if mat.quantity > 0:  # CHECK SO LUONG SU DUNG > 0
                quantity_on_hand = self.env['stock.quant']._get_available_quantity(mat.product_id.product_id,
                                                                                   room.location_supply_stock)  # check quantity trong location
                if mat.uom_id != mat.product_id.uom_id:
                    mat.write({'quantity': mat.uom_id._compute_quantity(mat.quantity, mat.product_id.uom_id),
                               'uom_id': mat.product_id.uom_id.id})  # quy so suong su dung ve don vi chinh cua san pham

                if quantity_on_hand < mat.quantity:
                    validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
                        mat.product_id.default_code, mat.product_id.name, str(quantity_on_hand), str(mat.uom_id.name),
                        room.location_supply_stock.name)
                else:  # truong one2many trong stock picking de tru cac product trong inventory
                    vals.append({
                        'name': 'THBN: ' + mat.product_id.product_id.name,
                        'origin': str(self.walkin.id) + "-" + str(self.walkin.service.ids),  # mã pk-mã dịch vụ
                        'date': date_done,
                        'company_id': self.env.company.id,
                        'date_expected': date_done,
                        'product_id': mat.product_id.product_id.id,
                        'product_uom_qty': mat.quantity,
                        'product_uom': mat.uom_id.id,
                        'location_id': room.location_supply_stock.id,
                        'location_dest_id': self.patient.partner_id.property_stock_customer.id,
                        'partner_id': self.patient.partner_id.id,
                        # xuat cho khach hang/benh nhan nao
                    })

        # neu co vat tu tieu hao
        if vals and validate_str == '':
            # tao phieu xuat kho
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
                                                                  ('warehouse_id', '=',
                                                                   self.institution.warehouse_ids[0].id)],
                                                                 limit=1).id
            # picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
            #                                                       ('warehouse_id', '=',
            #                                                        self.env.ref('stock.warehouse0').id)],
            #                                                      limit=1).id
            pick_note = 'THBN - %s - %s' % (self.name, self.walkin.name)
            pick_vals = {'note': pick_note,
                         'origin': pick_note,
                         'partner_id': self.patient.partner_id.id,
                         'patient_id': self.patient.id,
                         'picking_type_id': picking_type,
                         'location_id': room.location_supply_stock.id,
                         'location_dest_id': self.patient.partner_id.property_stock_customer.id,
                         # xuat cho khach hang/benh nhan nao
                         'date_done': date_done,
                         # 'immediate_transfer': True,  # sẽ gây lỗi khi dùng lô, pick với immediate_transfer sẽ ko cho tạo move, chỉ tạo move line
                         # 'move_ids_without_package': vals
                         }
            fail_pick_name = self.env['stock.picking'].search(
                [('origin', 'ilike', 'THBN - %s - %s' % (self.name, self.walkin.name))], limit=1).name
            if fail_pick_name:
                pick_vals['name'] = fail_pick_name.split('-', 1)[0]
            stock_picking = self.env['stock.picking'].create(pick_vals)
            for move_val in vals:
                move_val['name'] = stock_picking.name + " - " + move_val['name']
                move_val['picking_id'] = stock_picking.id
                self.env['stock.move'].create(move_val)
            # KO TU DONG XUAT KHO NUA MA CHI TAO PHIEU XUAT THOI
            stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
            for move_line in stock_picking.move_ids_without_package:
                for move_live_detail in move_line.move_line_ids:
                    move_live_detail.qty_done = move_live_detail.product_uom_qty
                # move_line.quantity_done = move_line.product_uom_qty
            stock_picking.with_context(
                force_period_date=date_done).sudo().button_validate()  # ham tru product trong inventory, sudo để đọc stock.valuation.layer

            # sua ngay hoan thanh
            for move_line in stock_picking.move_ids_without_package:
                move_line.move_line_ids.write({'date': date_done})  # sửa ngày hoàn thành ở stock move line
            stock_picking.move_ids_without_package.write(
                {'date': date_done})  # sửa ngày hoàn thành ở stock move
            stock_picking.date_done = date_done
            stock_picking.sci_date_done = date_done

            stock_picking.create_date = self.date_analysis
            # Cập nhật ngược lại picking_id vào mats để truyền số liệu sang vật tư phiếu khám
            self.imaging_material_ids.write({'picking_id': stock_picking.id})

        elif validate_str != '':
            raise ValidationError(_(
                "Các loại Vật tư sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))

        # log access patient
        # data_log = self.env['sh.medical.patient.log'].search([('walkin', '=', self.walkin.id)])
        # data_cdha = False
        # for data in data_log:
        #     # nếu đã có data log cho khoa xn này rồi
        #     if data.department.id == self.department.id:
        #         data_cdha = data
        #     # nếu có log khoa KB rồi thì cập nhật ngày ra cho khoa kb là ngày bắt đầu làm dịch vụ
        #     # if data.department.type == 'Examination':
        #     #     data.date_out = self.services_date
        # # nếu chưa có data log=> tạo log
        # if not data_cdha:
        #     vals_log = {'walkin': self.walkin.id,
        #                 'patient': self.patient.id,
        #                 'department': self.department.id,
        #                 'date_in': self.date_analysis if self.date_analysis else datetime.datetime.now()}
        #     self.env['sh.medical.patient.log'].create(vals_log)
        # else:
        #     data_cdha.date_in = self.date_analysis if self.date_analysis else datetime.datetime.now()
        #     data_cdha.date_out = self.date_done if self.date_done else datetime.datetime.now()

        # cập nhật trạng thái phiếu CDHA
        res = self.write({'state': 'Completed', 'date_done': date_done})

        # cap nhat vat tu cho phieu kham
        self.walkin.update_walkin_material(mats_types=['Imaging'])

        # update so CDHA hoan thanh
        img_done = self.env['sh.medical.imaging'].search_count(
            [('walkin', '=', self.walkin.id), ('state', '=', 'Completed')])
        img_total = self.env['sh.medical.imaging'].search_count(
            [('walkin', '=', self.walkin.id), ('state', '!=', 'Cancelled')])
        self.walkin.write(
            {'img_test_done_count': img_done, 'has_img_result': True if img_total - img_done == 0 else False})

        # return res

    #
    # def set_to_test_cancelled(self):
    #     return self.write({'state': 'Cancelled'})

    def _default_account(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.default_credit_account_id.id

    #
    # def action_imaging_invoice_create(self):
    #     invoice_obj = self.env["account.invoice"]
    #     invoice_line_obj = self.env["account.invoice.line"]
    #     inv_ids = []
    #     inv_line_ids = []
    #
    #     for imaging in self:
    #         # Create Invoice
    #         if imaging.patient:
    #             curr_invoice = {
    #                 'partner_id': imaging.patient.partner_id.id,
    #                 'account_id': imaging.patient.partner_id.property_account_receivable_id.id,
    #                 'patient': imaging.patient.id,
    #                 'state': 'draft',
    #                 'type':'out_invoice',
    #                 'date_invoice': datetime.date.today(),
    #                 'origin': "Imaging Test# : " + imaging.name,
    #                 'target': 'new',
    #             }
    #
    #             inv_ids = invoice_obj.create(curr_invoice)
    #
    #             if inv_ids:
    #                 inv_id = inv_ids.id
    #                 prd_account_id = self._default_account()
    #                 if imaging.test_type:
    #
    #                     # Create Invoice line
    #                     curr_invoice_line = {
    #                         'name': "Charge for " + str(imaging.test_type.name) + " Imaging test",
    #                         'price_unit': imaging.test_type.test_charge or 0,
    #                         'quantity': 1.0,
    #                         'account_id': prd_account_id,
    #                         'invoice_id': inv_id,
    #                     }
    #
    #                     inv_line_ids = invoice_line_obj.create(curr_invoice_line)
    #
    #             self.write({'state': 'Invoiced'})
    #
    #     return {
    #             'domain': "[('id','=', " + str(inv_id) + ")]",
    #             'name': 'Imaging Test Invoice',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             'res_model': 'account.invoice',
    #             'type': 'ir.actions.act_window'
    #     }

    @api.onchange('institution')
    def _onchange_institution(self):
        # set khoa mac dinh la khoa cdha cua co so y te
        if self.institution:
            lab_dep = self.env['sh.medical.health.center.ward'].search(
                [('institution', '=', self.institution.id), ('type', '=', 'Imaging')], limit=1)
            self.department = lab_dep

    # @api.onchange('department')
    # def _onchange_department(self):
    #     if not self.institution:
    #         self.institution = self.department.institution.id
    #     self.test_type = ''

    # Fetching imaging test types
    @api.onchange('test_type')
    def onchange_test_type_id(self):
        self.imaging_material_ids = False
        self.group_type = self.test_type.group_type if self.test_type else False
        # self.perform_room = self.test_type.perform_room if self.test_type else False
        # self.department = self.perform_room.department if self.perform_room else False
        values = self.onchange_test_type_id_values(self.test_type.id if self.test_type else False)
        return values

    def onchange_test_type_id_values(self, test_type):
        ### set value for material test by type ###
        # imaging_obj = self.env['sh.medical.imaging.test.type.material']
        imaging_ids = []

        res = {}

        # if no test type present then nothing will process
        if not test_type:
            return res

        imaging_type = self.env['sh.medical.imaging.test.type'].browse(test_type)

        # defaults
        res = {'value': {
            'imaging_material_ids': [],
            'analysis': '',
            'conclusion': '',
        }
        }

        # Getting lab test lines values
        query_material = _(
            "select  sequence, product_id, quantity , uom_id from sh_medical_imaging_test_type_material where imaging_types_id=%s") % (
                             str(test_type))
        self.env.cr.execute(query_material)
        vals = self.env.cr.fetchall()
        if vals:
            for va in vals:
                specs = {
                    'sequence': va[0],
                    'product_id': va[1],
                    'init_quantity': va[2],
                    'quantity': va[2],
                    'is_init': True,
                    'uom_id': va[3],
                }
                imaging_ids += [specs]

        res['value'].update({
            'imaging_material_ids': imaging_ids,
            'analysis': imaging_type.analysis,
            'conclusion': imaging_type.conclusion,
        })
        return res


class shealthImagingMaterial(models.Model):
    _name = 'sh.medical.imaging.material'
    _description = 'All material of the Imaging Test'
    _order = "sequence"

    MEDICAMENT_TYPE = [
        ('Medicine', 'Medicine'),
        ('Supplies', 'Supplies'),
        ('CCDC', 'CCDC')
    ]

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự
    imaging_id = fields.Many2one('sh.medical.imaging', string='Imaging Test')
    product_id = fields.Many2one('sh.medical.medicines', string='Tên', required=True,
                                 domain=lambda self: [('categ_id', 'child_of',
                                                       self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    init_quantity = fields.Float('Initial Quantity',
                                 digits='Product Unit of Measure',
                                 readonly=True)  # số lượng bom ban đầu của vật tư
    is_init = fields.Boolean('Is Initial', default=False)
    quantity = fields.Float('Quantity',
                            digits='Product Unit of Measure')  # số lượng sử dụng vật tư
    qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
                             compute='compute_available_qty_supply')

    location_id = fields.Many2one('stock.location', 'Tủ xuất',
                                  domain="[('location_institution_type', 'in', ['medicine','supply'])]")

    medicament_type = fields.Selection(MEDICAMENT_TYPE, related="product_id.medicament_type", string='Medicament Type',
                                       store=True)

    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')

    picking_id = fields.Many2one('stock.picking', string='Phiếu điều chuyển')

    @api.depends('product_id')
    def compute_available_qty_supply(self):
        for record in self:
            record.qty_avail = record.product_id.qty_available if record.product_id else 0

    @api.onchange('product_id')
    def _change_product_id(self):
        domain = {'domain': {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}
        institution = self.imaging_id.institution
        room = self.imaging_id.perform_room
        self.uom_id = self.product_id.uom_id
        if self.product_id and self.imaging_id and room and institution:
            if self.medicament_type == 'Medicine':
                self.location_id = room.location_medicine_stock
                domain['domain']['location_id'] = [('location_institution_type', '=', 'medicine'),
                                                   ('company_id', '=', institution.his_company.id)]
            elif self.medicament_type == 'Supplies':
                self.location_id = room.location_supply_stock
                domain['domain']['location_id'] = [('location_institution_type', '=', 'supply'),
                                                   ('company_id', '=', institution.his_company.id)]
        return domain

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.product_id.uom_id.category_id:
            self.uom_id = self.product_id.uom_id
            raise Warning(
                _('The Imaging Test Unit of Measure and the Material Unit of Measure must be in the same category.'))


# Inheriting Ward module to add "Imaging" screen reference
class SHealthWard(models.Model):
    _inherit = 'sh.medical.health.center.ward'

    imaging = fields.One2many('sh.medical.imaging', 'department', string='Imaging')
    count_img_not_completed = fields.Integer('Imaging not completed', compute="_count_img_not_completed")

    def _count_img_not_completed(self):
        oe_imgs = self.env['sh.medical.imaging']
        for ls in self:
            domain = [('state', '!=', 'Completed'), ('department', '=', ls.id)]
            ls.count_img_not_completed = oe_imgs.search_count(domain)
        return True
