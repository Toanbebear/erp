##############################################################################
#    Copyright (C) 2018 shealth (<http://scigroup.com.vn/>). All Rights Reserved
#    shealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, shealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

from odoo import fields, api, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
import datetime
from datetime import timedelta, date
import logging
from lxml import etree
import json

_logger = logging.getLogger(__name__)


# def num2words_vnm(num):
#     under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
#                 'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
#     tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
#     above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}
#
#     if num < 20:
#         return under_20[num]
#
#     elif num < 100:
#         under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
#         result = tens[num // 10 - 2]
#         if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
#             result += ' ' + under_20[num % 10]
#         return result
#
#     else:
#         unit = max([key for key in above_100.keys() if key <= num])
#         result = num2words_vnm(num // unit) + ' ' + above_100[unit]
#         if num % unit != 0:
#             if num > 1000 and num % unit < unit / 10:
#                 result += ' không trăm'
#             if 1 < num % unit < 10:
#                 result += ' linh'
#             result += ' ' + num2words_vnm(num % unit)
#     return result.capitalize()


class WalkinImage(models.Model):
    _name = 'sh.medical.walkin.image'
    _description = 'Ảnh trong phiếu khám'

    name = fields.Char('Tên')
    image = fields.Binary('Ảnh', attachment=True)
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', 'Phiếu khám liên quan', copy=True)


class SHealthWalkinMaterial(models.Model):
    _name = 'sh.medical.walkin.material'
    _description = 'All material of the Walkin'

    NOTE = [
        ('Labtest', 'Material of Labtest'),
        ('Imaging', 'Material of Imaging'),
        ('Surgery', 'Material of Surgery'),
        ('Specialty', 'Material of Specialty Service'),
        ('Inpatient', 'Material of Inpatient'),
        ('Evaluation', 'Material of Evaluation'),
        ('Medicine', 'Thuốc cấp về'),
        # ('Extra', 'Material of Extra Service'),
    ]

    @api.model
    def _select_target_model(self):
        models = self.env['ir.model'].search([('model', 'in', ['sh.medical.lab.test', 'sh.medical.imaging', 'sh.medical.specialty',
                                                               'sh.medical.surgery', 'sh.medical.evaluation', 'sh.medical.inpatient',
                                                               'sh.medical.patient.rounding', 'sh.medical.patient.instruction', 'sh.medical.prescription'])])
        return [(model.model, model.name) for model in models]

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự
    imaging_id = fields.Many2one('sh.medical.imaging', string='Imaging Test')
    product_id = fields.Many2one('sh.medical.medicines', string='Product', required=True,
                                 domain=lambda self: [('categ_id', 'child_of',
                                                       self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    init_quantity = fields.Float('Initial Quantity',
                                 digits='Product Unit of Measure')  # số lượng bom ban đầu của vật tư
    quantity = fields.Float('Quantity',
                            digits='Product Unit of Measure')  # số lượng sử dụng vật tư
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    note = fields.Selection(NOTE, 'Material note')
    interner_note = fields.Char('Interner note')
    is_readonly = fields.Boolean('Is readonly', default=False)

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', readonly=True)

    patient = fields.Many2one('sh.medical.patient', string='Bệnh nhân', related="walkin.patient", store=True)

    institution = fields.Many2one('sh.medical.health.center', string='Health Center', required=True)
    department = fields.Many2one('sh.medical.health.center.ward', string='Department', required=True)
    location_id = fields.Many2one('stock.location', 'Tủ xuất')
    date_out = fields.Datetime(string='Ngày xuất')

    services = fields.Many2many('sh.medical.health.center.service', track_visibility='onchange', string='Dịch vụ thực hiện')

    ref_id = fields.Reference(selection='_select_target_model', string='Mã phiếu')  # Link đến các phiếu bệnh viện
    picking_id = fields.Many2one('stock.picking', string='Phiếu điều chuyển')
    lot_id = fields.Many2one('stock.production.lot', string='Số lô')
    removal_date = fields.Datetime('Hạn sử dụng', related='lot_id.removal_date')

    _order = "sequence"

    @api.onchange('product_id')
    def _change_product_id(self):
        self.uom_id = self.product_id.uom_id

        return {'domain': {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.product_id.uom_id.category_id:
            self.uom_id = self.product_id.uom_id
            raise Warning(
                _('The Walkin Unit of Measure and the Material Unit of Measure must be in the same category.'))

    @api.model
    def cron_remove_materials_none_walkin(self):
        walkin_material = self.env['sh.medical.walkin.material'].sudo().search([('walkin', '=', False)])
        walkin_material.unlink()


class SHealthPatientLog(models.Model):
    _name = 'sh.medical.patient.log'
    _description = 'All log access Room of the patient'

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #')
    patient = fields.Many2one('sh.medical.patient', string='Patient')
    department = fields.Many2one('sh.medical.health.center.ward', string='Department access')

    date_in = fields.Datetime('Date in')
    date_out = fields.Datetime('Date out')

    _order = "date_in"

class SHealthWalkinAdvisoryServices(models.Model):
    _name = 'sh.medical.walkin.advisory.services'
    _description = 'Bảng tư vấn dịch vụ thực hiện ở phiếu khám'

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')
    service_advisory = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ')
    desire = fields.Text('Mong muốn của khách hàng')
    current_state = fields.Text('Tình trạng hiện tại của khách hàng')

class SHealthAppointmentWalkin(models.Model):
    _name = "sh.medical.appointment.register.walkin"
    _description = "Information of Walkin"
    _inherit = ['mail.thread', 'money.mixin']

    _order = "date desc"

    MARITAL_STATUS = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Widowed', 'Widowed'),
        ('Divorced', 'Divorced'),
        ('Separated', 'Separated'),
    ]

    SEX = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    BLOOD_TYPE = [
        ('A', 'A'),
        ('B', 'B'),
        ('AB', 'AB'),
        ('O', 'O'),
    ]

    RH = [
        ('+', '+'),
        ('-', '-'),
    ]

    WALKIN_STATUS = [
        ('Scheduled', 'Khám'),
        ('WaitPayment', 'Chờ thu tiền'),
        ('Payment', 'Đã thu tiền'),
        ('InProgress', 'Đang thực hiện'),
        ('Completed', 'Hoàn thành'),
        ('Cancelled', 'Đã hủy'),
        # ('Invoiced', 'Invoiced'),
    ]

    TYPE_CHECK = [
        ('Advisory', 'Tư vấn'),
        # ('Recheck', 'Tái khám'),
        ('Guarantee', 'Bảo hành'),
        # ('Hospitalize', 'Nhập viện'),
    ]

    HANDLE = [
        ('discharge', 'Ra viện'),
        ('outpatient', 'Điều trị ngoại trú'),
        ('allow', 'Xin về'),
        ('escaped', 'Trốn viện'),
        ('transit', 'Chuyển tuyến'),
        ('dead', 'Tử vong'),
    ]

    LEVEL = [
        ('5', 'Khách hàng V.I.P'),
        ('4', 'Đặc biệt'),
        ('3', 'Quan tâm hơn'),
        ('2', 'Quan tâm'),
        ('1', 'Bình thường')
    ]

    ROOM_TYPE = [
        # ('Examination', 'Khám bệnh'),
        # ('Laboratory', 'Xét nghiệm'),
        # ('Imaging', 'Chuẩn đoán hình ảnh'),
        ('Surgery', 'Phẫu thuật'),
        # ('Inpatient', 'Lưu bệnh nhân'),
        ('Spa', 'Spa'),
        ('Laser', 'Laser'),
        ('Odontology', 'Nha')
    ]

    def _get_physician(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    def get_physician_kb(self):
        # if self.env.ref('__import__.khn_medical_job_kb', False):
        #     return [('is_pharmacist', '=', False), ('job_id', '=', self.env.ref('__import__.khn_medical_job_kb').id)]
        # else:
        #     return [('is_pharmacist', '=', False)]
        # return [('is_pharmacist', '=', False), ('speciality', 'not in', [self.env.ref('shealth_all_in_one.49').id,self.env.ref('shealth_all_in_one.23').id,self.env.ref('shealth_all_in_one.33').id])]
        return [('is_pharmacist', '=', False), ('speciality', 'not in', [7, 3, 4])]

    def get_nurse_kb(self):
        # chỉ lấy các physician có chuyên môn là điều dưỡng
        # return [('is_pharmacist', '=', False), ('speciality', '=', [self.env.ref('shealth_all_in_one.33').id,self.env.ref('shealth_all_in_one.11').id,self.env.ref('shealth_all_in_one.51').id,self.env.ref('shealth_all_in_one.60').id])]
        return [('is_pharmacist', '=', False), ('speciality', '=', [4, 2, 8, 9])]

    name = fields.Char(string='Queue #', size=128, required=True, default=lambda *a: '/',
                       states={'Completed': [('readonly', True)]}, track_visibility='always')
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True,
                              readonly=False, states={'Completed': [('readonly', True)]})
    partner_id = fields.Many2one('res.partner', string='Đối tác', related="patient.partner_id", store=True, index=True)
    dob = fields.Date(string='Date of Birth', related="patient.birth_date", store=True, track_visibility='onchange')
    sex = fields.Selection(SEX, string='Sex', related="patient.gender", store=True, track_visibility='onchange')
    marital_status = fields.Selection(MARITAL_STATUS, string='Marital Status', related="patient.marital_status",
                                      store=True, track_visibility='onchange')
    blood_type = fields.Selection(BLOOD_TYPE, string='Blood Type', related="patient.blood_type", store=True,
                                  track_visibility='onchange')
    rh = fields.Selection(RH, string='Rh', readonly=False, related="patient.rh", store=True,
                          track_visibility='onchange')
    doctor = fields.Many2one('sh.medical.physician', string='Responsible Physician', readonly=False,
                             states={'Completed': [('readonly', True)]},
                             domain=lambda self: self.get_physician_kb(),
                             default=_get_physician, track_visibility='onchange')
    doctor_name = fields.Char('Tên bác sỹ', related='doctor.name', store=True)  # lưu tên bác sỹ để xuất phiếu khám
    state = fields.Selection(WALKIN_STATUS, string='State', readonly=False, states={'Completed': [('readonly', True)]},
                             default=lambda *a: 'Scheduled', track_visibility='onchange')
    comments = fields.Text(string='Comments', readonly=False, states={'Completed': [('readonly', True)]},
                           track_visibility='onchange')
    date = fields.Datetime(string='Day of the examination', compute="_compute_date", required=True, store=True, index=True,
                           readonly=False, states={'Completed': [('readonly', True)]},
                           default=lambda self: fields.Datetime.now(), track_visibility='onchange')
    # evaluation_ids = fields.One2many('sh.medical.evaluation', 'walkin', string='Evaluation', readonly=False,
    #                                  states={'Completed': [('readonly', True)]})
    prescription_ids = fields.One2many('sh.medical.prescription', 'walkin', string='Prescriptions', readonly=False,
                                       states={'Completed': [('readonly', True)]})
    lab_test_ids = fields.One2many('sh.medical.lab.test', 'walkin', string='Lab Tests', readonly=False,
                                   states={'Completed': [('readonly', True)]})
    imaging_ids = fields.One2many('sh.medical.imaging', 'walkin', string='Imaging Tests', readonly=False,
                                  states={'Completed': [('readonly', True)]})
    surgeries_ids = fields.One2many('sh.medical.surgery', 'walkin', string='Surgeries Tests', readonly=False,
                                    states={'Completed': [('readonly', True)]})
    specialty_ids = fields.One2many('sh.medical.specialty', 'walkin', string='Specialty Tests', readonly=False,
                                    states={'Completed': [('readonly', True)]})
    inpatient_ids = fields.One2many('sh.medical.inpatient', 'walkin', string='Inpatient Admissions', readonly=False,
                                    states={'Completed': [('readonly', True)]})

    reexam_ids = fields.One2many('sh.medical.reexam', 'walkin', string='Lịch tái khám - Hướng dẫn', readonly=False,
                                 states={'Completed': [('readonly', True)]})
    # vaccine_ids = fields.One2many('sh.medical.vaccines', 'walkin', string='Vaccines', readonly=False, states={'Completed': [('readonly', True)]})

    institution = fields.Many2one('sh.medical.health.center', string='Health Center', required=True, readonly=False,
                                  states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    department = fields.Many2one('sh.medical.health.center.ward', string='Department',
                                 help="Department of the selected Health Center",
                                 domain="[('institution','=',institution)]", readonly=False,
                                 states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    related_department = fields.Many2one('sh.medical.health.center.ward', string='Khoa điều trị',
                                 help="Khoa điều trị", readonly=False,
                                 states={'Completed': [('readonly', True)]}, track_visibility='onchange', related="service_room.related_department")
    # reason_check = fields.Selection(REASON_CHECK, 'Reason Check', readonly=False, states={'Completed': [('readonly', True)]}, default=lambda *a: 'Advisory', track_visibility='onchange')
    type_crm_id = fields.Many2one('crm.type', string="Loại phiếu khám", readonly=False, default=lambda self: self.env.ref('crm_base.type_oppor_new').id,
                                   states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    reason_check = fields.Text('Lý do vào viện', related="reception_id.reason", readonly=False,
                               states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    # service = fields.Many2one('sh.medical.health.center.service', string='Service', readonly=False, states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    service = fields.Many2many('sh.medical.health.center.service', 'sh_walkin_service_rel', 'walkin_id', 'service_id',
                               readonly=False, states={'Completed': [('readonly', True)]}, track_visibility='onchange',
                               string='Services')
    service_room = fields.Many2one('sh.medical.health.center.ot', string='Room perform',
                                   domain="[('department', '=', department)]", readonly=False,
                                   states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    service_confirm = fields.Many2many('sh.medical.health.center.service', 'sh_walkin_service_confirm_rel', 'walkin_id',
                                       'service_id', readonly=True, track_visibility='onchange',
                                       string='Dịch vụ đã xác nhận')
    service_expected = fields.Many2many('sh.medical.health.center.service', 'sh_walkin_service_expected_rel',
                                        'walkin_id', 'service_id', readonly=True, track_visibility='onchange',
                                        string='Services Expected')
    date_re_exam = fields.Datetime(string='Date Re-exam', readonly=False, states={'Completed': [('readonly', True)]},
                                   track_visibility='onchange')
    date_out = fields.Datetime(string='Ngày ra viện', readonly=False, states={'Completed': [('readonly', True)]},
                               track_visibility='onchange')
    close_walkin = fields.Date(string='Ngày đóng phiếu')
    service_date = fields.Datetime(string='Ngày dự kiến làm dịch vụ', readonly=True, states={'Completed': [('readonly', True)]},
                               track_visibility='onchange')
    # taskmaster = fields.Many2one('res.users', string='Taskmaster', readonly=True, track_visibility='onchange')
    service_date_start = fields.Datetime(string='Ngày làm dịch vụ', compute="_compute_service_date_start", store=True,
                           index=True, track_visibility='onchange')
    doctor_order = fields.Many2one('sh.medical.physician', string='Trưởng ekip phẫu thuật', domain="[('is_doctor_order','=', True)]", help="Bác sĩ được khách hàng yêu cầu")

    # thong tin vat tu
    material_ids = fields.One2many('sh.medical.walkin.material', 'walkin', string="Material Information")

    # patient_log = fields.One2many('sh.medical.patient.log', 'walkin', string='History')

    # liên kết reception
    reception_id = fields.Many2one('sh.reception', string='Reception')

    # count
    lab_test_count = fields.Integer('Lab test count', compute="count_lab_test", compute_sudo=False, store=True)
    img_test_count = fields.Integer('Imaging test count', compute="count_img_test", store=True)
    surgery_count = fields.Integer('Surgery count', compute="count_surgery", store=True)
    specialty_count = fields.Integer('Specialty count', compute="count_specialty", store=True)

    lab_test_done_count = fields.Integer('Lab test completed count', readonly=True)
    img_test_done_count = fields.Integer('Imaging completed test count', readonly=True)
    surgery_done_count = fields.Integer('Surgery Done count', readonly=True)
    specialty_done_count = fields.Integer('Specialty Done count', readonly=True)

    # has_lab_result = fields.Boolean('Đã có KQ XN', readonly=True, compute='count_lab_test')  # không dùng nữa, sẽ xóa ở lần sau để tránh lỗi
    # TODO Xem xét việc store lại trường has_processing_lab
    has_processing_lab = fields.Boolean('Có XN đang thực hiện', readonly=True,
                                        compute='count_lab_test', 
                                        compute_sudo=False, search='_search_has_processing_lab')
    has_img_result = fields.Boolean('Đã có KQ CĐHA', readonly=True, store=True)

    # money_spent = fields.Float('Money spent', compute="sum_money_spent")

    pathology = fields.Many2one('sh.medical.pathology', string='Condition', help="Base Condition / Reason",
                                readonly=False, states={'Completed': [('readonly', True)]})

    is_over_material = fields.Boolean('Over material', default=False)
    user_approval = fields.Many2one('res.users', string='User approval', readonly=True, track_visibility='onchange')

    # phiếu khám gốc
    root_walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Root walkin',
                                  domain="[('patient','=',patient)]",
                                  hint="Phiếu khám gốc của phiếu khám bảo hành",
                                  states={'Completed': [('readonly', True)]}, track_visibility='onchange')

    booking_id = fields.Many2one('crm.lead')
    sale_order_id = fields.Many2one('sale.order')
    code_booking = fields.Char(string='Mã booking tương ứng', related='booking_id.code_booking')
    allow_institutions = fields.Many2many('sh.medical.health.center', string='Allow institutions', compute='_get_allow_institutions')
    is_missing_money = fields.Boolean(string='Thiếu tiền thực hiện?', compute='_check_missing_money')

    # user_domain = fields.Many2many('res.users', string='User domain', compute='_get_user_domain', store=True)

    # patient_level = fields.Selection(LEVEL, string='Loại', index=True, default='1', related="partner_id.customer_classification", store=True, readonly=False)
    patient_level = fields.Selection(LEVEL, string='Loại', index=True, default='1', store=True, readonly=False)

    company_id = fields.Many2one('res.company', string='Công ty chính',
                                 related="booking_id.company_id",
                                 store=True,
                                 ondelete='cascade')
    company2_id = fields.Many2many('res.company', 'sh_walkin_company_related_rel', 'walkin_id', 'company_id',
                                   string='Công ty share',
                                   related="booking_id.company2_id",
                                   store=True,
                                   readonly=True,
                                   ondelete='cascade')

    note = fields.Text('Ghi chú', states={'Completed': [('readonly', True)]})

    room_type = fields.Selection(ROOM_TYPE, string='Loại phòng khám', related="service_room.related_department.type",
                                      store=False, track_visibility='onchange')
    # session_num = fields.Integer('Lần thực hiện', help="Lần thứ mấy khách đến thực hiện dịch vụ liệu trình")
    reception_nurse = fields.Many2one('sh.medical.physician', string='Điều dưỡng đón tiếp', readonly=False,
                             states={'Completed': [('readonly', True)]},
                             domain=lambda self: self.get_nurse_kb(),
                             default=_get_physician, track_visibility='onchange')

    teeths = fields.Many2many('sh.medical.teeth', 'sh_walkin_teeth_related_rel', 'walkin_id', 'teeth_id',
                                   string='Mã răng')

    # @api.constrains('close_walkin', 'create_date')
    # def validate_close_walkin(self):
    #     for record in self:
    #         if record.close_walkin and (record.close_walkin > (record.create_date + timedelta(weeks=8)).date()):
    #             raise ValidationError('Ngày đóng phiếu khám không hợp lệ.')

    # @api.constrains('close_walkin', 'date_out')
    # def validate_date_out(self):
    #     for record in self:
    #         if record.date_out and record.close_walkin and (record.date_out > (record.close_walkin + timedelta(weeks=4))):
    #             raise ValidationError('Ngày ra viện khám không hợp lệ.')


    def print_service_info_sheet(self):
        return self.env.ref('shealth_all_in_one.action_service_info_sheet').report_action(self)

    def print_report_hospital_discharge_sheet(self):
        return self.env.ref('shealth_all_in_one.action_report_hospital_discharge_sheet').report_action(self)

    @api.depends('surgeries_ids.state', 'specialty_ids.state')
    def _compute_service_date_start(self):
        """
        Tính toán ngày làm dịch vụ dựa trên phiếu CK/PTTT
            Sau khi người dùng Hoàn thành phiếu Chuyên khoa/Phẫu thuật thủ thuật
            => "Ngày làm Dịch vụ" tự động bắt theo "Ngày giờ bắt đầu" (services_date/surgery_date)
            Trường hợp có nhiều phiếu CK/PTTT thì lấy theo "Ngày giờ bắt đầu" đầu tiên
        """
        for record in self:
            if record.surgeries_ids and record.surgeries_ids[0].state == 'Done':
                record.service_date_start = record.surgeries_ids[0].surgery_date
            if record.specialty_ids and record.specialty_ids[0].state == 'Done':
                record.service_date_start = record.specialty_ids[0].services_date

    @api.depends('sale_order_id.amount_total', 'sale_order_id.amount_remain','sale_order_id.amount_owed')
    def _check_missing_money(self):
        for record in self.with_env(self.env(su=True)):
            record.is_missing_money = True
            if (record.state not in ['WaitPayment','Completed']) and (record.sale_order_id.state in ['draft','sent']) and (record.sale_order_id.amount_total > 0) \
                    and (record.sale_order_id.amount_total > (record.sale_order_id.amount_remain + record.sale_order_id.amount_owed)):
                record.is_missing_money = True
            else:
                if record.state in ['Scheduled']:
                    record.set_to_progress()
                record.is_missing_money = False

    @api.depends('booking_id')
    def _get_allow_institutions(self):
        for record in self.with_env(self.env(su=True)):
            companies = record.booking_id.company_id + record.booking_id.company2_id
            institutions = self.env['sh.medical.health.center'].search([('his_company', 'in', companies.ids)])
            record.allow_institutions = [(6, 0, institutions.ids)]

    # @api.depends('service_room.related_department.physician.sh_user_id')
    # def _get_user_domain(self):
    #     for record in self:
    #         record.user_domain = record.service_room.related_department.physician.sh_user_id

    @api.onchange('root_walkin')
    def onchange_root_walkin(self):
        if self.root_walkin:
            self.pathological_process = self.root_walkin.pathological_process
            self.surgery_history = self.root_walkin.surgery_history
            self.allergy_history = self.root_walkin.allergy_history
            self.family_history = self.root_walkin.family_history
            self.physical_exam = self.root_walkin.physical_exam
            self.cyclic_info = self.root_walkin.cyclic_info
            self.respiratory_exam = self.root_walkin.respiratory_exam
            self.digest_exam = self.root_walkin.digest_exam
            self.reins_exam = self.root_walkin.reins_exam
            self.nerve_exam = self.root_walkin.nerve_exam
            self.other_exam = self.root_walkin.other_exam
            self.specialty_exam = self.root_walkin.specialty_exam
            self.temperature = self.root_walkin.temperature
            self.systolic = self.root_walkin.systolic
            self.respiratory_rate = self.root_walkin.respiratory_rate
            self.bpm = self.root_walkin.bpm
            self.weight = self.root_walkin.weight
            self.height = self.root_walkin.height
            # self.service = self.root_walkin.service

    # trường ẩn hiện phiếu pttt theo dịch vụ
    flag_surgery = fields.Boolean('Flag surgery', default=False)

    handle = fields.Selection(HANDLE, string='Handle', readonly=False, states={'Completed': [('readonly', True)]},
                              track_visibility='onchange')

    payment_ids = fields.One2many('account.payment', 'walkin', string='Phiếu thu')
    lock = fields.Boolean('Khóa phiếu')

    index_by_day = fields.Integer('Số thứ tự', compute="_compute_date_to_index", store=True)

    walkin_image_ids = fields.One2many('sh.medical.walkin.image', 'walkin', string='Images')

    doctor_surgeon = fields.Many2one('sh.medical.physician', string='Bác sĩ phẫu thuật')
    doctor_anesthetist = fields.Many2one('sh.medical.physician', string='Bác sĩ gây mê')

    # doctor_surgeon = fields.Many2one('sh.medical.physician', string='Bác sĩ phẫu thuật',
    #                                  compute="_compute_doctor_surgeon", store=True)
    # doctor_anesthetist = fields.Many2one('sh.medical.physician', string='Bác sĩ gây mê',
    #                                      compute="_compute_doctor_surgeon", store=True)

    # @api.depends('surgeries_ids')
    # def _compute_doctor_surgeon(self):
    #     for record in self:
    #         if record.surgeries_ids:
    #             record.doctor_surgeon = record.surgeries_ids[0].surgeon
    #             record.doctor_anesthetist = record.surgeries_ids[0].anesthetist
    #         else:
    #             record.doctor_surgeon = False
    #             record.doctor_anesthetist = False

    def _get_specialty_exam(self):
        return self.reason_check

    # thông tin khám
    pathological_process = fields.Text('Quá trình bệnh lý')
    surgery_history = fields.Text('Tiền sử ngoại khoa', default="Không")
    medical_history = fields.Text('Tiền sử nội khoa', default="Không")
    allergy_history = fields.Text('Tiền sử dị ứng', default="Không")
    family_history = fields.Text('Tiền sử gia đình', default="Không")
    physical_exam = fields.Text('Toàn thân',
                                default="""-	Thể trạng khá.\n-	Da không xanh , niêm mạc hồng.\n-	Tuyến giáp không to.\n-	Hạnh ngoại biên không sờ thấy.""")
    cyclic_info = fields.Text('Tuần hoàn', default="Nhịp tim đều : 0 lần/ phút, Tiếng tim T1T2 bình thường.")
    respiratory_exam = fields.Text('Hô hấp', default="Thở êm, rì rào phế nang đều rõ 2 bên.")
    digest_exam = fields.Text('Tiêu hóa', default="Bụng mềm, Gan lách không to.")
    reins_exam = fields.Text('Thận – Tiết niệu – Sinh dục', default="Khám sơ bộ bình thường.")
    nerve_exam = fields.Text('Thần kinh', default="Ý thức tốt, không có dấu hiệu thần kinh khu trú.")
    other_exam = fields.Text('Các cơ quan khác', default="chưa phát hiện dấu hiệu bệnh lý.")
    specialty_exam = fields.Text('Chuyên khoa')

    systolic = fields.Integer(string='Systolic Pressure')
    diastolic = fields.Integer(string='Diastolic Pressure')
    bpm = fields.Integer(string='Heart Rate', help="Heart rate expressed in beats per minute")
    respiratory_rate = fields.Integer(string='Respiratory Rate',
                                      help="Respiratory rate expressed in breaths per minute")
    temperature = fields.Float(string='Temperature (celsius)')
    weight = fields.Float(string='Weight (kg)')
    height = fields.Float(string='Height (cm)')
    bmi = fields.Float(string='Body Mass Index (BMI)')
    info_diagnosis = fields.Text(string='Chẩn đoán vào viện')
    directions = fields.Text(string='Plan')

    uom_price = fields.Integer(string='Số lượng thực hiện',
                                      help="Răng/cm2/...", default=1)

    # thông tin tư vấn:
    list_advisory_services = fields.One2many('sh.medical.walkin.advisory.services', 'walkin', string='Bảng Tư Vấn')
    level_of_improvement = fields.Boolean('Mức độ cải thiện')
    service_costs = fields.Boolean('Chi phí dịch vụ')
    other_costs_incurred = fields.Boolean('Chi phí phát sinh khác', help="Chi phí phát sinh khác: tiền giường khi ở lại bệnh viện, tiền giường người nhà…")
    warranty = fields.Boolean('Chế độ bảo hành và phiếu bảo hành')
    hospital_checkout = fields.Boolean('Giấy ra viện')
    therapy = fields.Boolean('Liệu trình')
    diet = fields.Boolean('Chế độ ăn')
    doctor_advice = fields.Text('Tư vấn của Bác sĩ')
    conclude = fields.Text('Kết luận')

    @api.onchange('uom_price','service')
    def onchange_uom_price(self):
        if self.uom_price < 0:
            raise ValidationError(_('Số lượng phải > 0'))

        check_duplicate = self.list_advisory_services.mapped('service_advisory').ids
        list_services_walkin = self.service._origin.ids
        # print(list_services_walkin)

        remove_ser = self.list_advisory_services.filtered(lambda ad_line: ad_line.service_advisory.id not in list_services_walkin)

        # remove_ser = [x for x in check_duplicate if x not in list_services_walkin]
        # print(remove_ser.service_advisory.name)

        list_advisory_services = [(2, ser.id) for ser in remove_ser]
        for ser in self.service:
            # print(ser._origin.id)
            ser_id = ser._origin.id

            # GET DATA PHIẾU TƯ VẤN TỪ BOOKING
            check_duplicate_booking = []
            adv_booking = self.booking_id.consultation_ticket_ids.mapped('consultation_detail_ticket_ids').filtered(
                lambda a: a.service_id.id == ser_id and a.confirm_service == True).sorted(reverse=True)
            # đã có data tư vấn ở booking
            if adv_booking:
                for adv in adv_booking:
                    # print(adv)
                    ser_booking_id = adv.service_id.id
                    if ser_booking_id not in check_duplicate_booking and ser_id not in check_duplicate:
                        check_duplicate_booking.append(ser_booking_id)
                        check_duplicate.append(ser_id)
                        list_advisory_services.append((0, 0, {
                            'walkin': self.id,
                            'service_advisory': ser_booking_id,
                            'desire': adv.desire,
                            'current_state': adv.health_status}))
            #dịch vụ mới phát sinh từ phiếu khám
            else:
                if ser_id not in check_duplicate:
                    check_duplicate.append(ser_id)
                    list_advisory_services.append((0, 0, {
                        'walkin': self.id,
                        'service_advisory': ser_id,
                        'desire': 'mong muốn',
                        'current_state': 'tình trạng'}))
        # print(list_advisory_services)
        self.list_advisory_services = list_advisory_services

    @api.onchange('bpm')
    def onchange_bpm(self):
        self.cyclic_info = "Nhịp tim đều : %s lần/ phút, Tiếng tim T1T2 bình thường." % str(self.bpm)

    @api.onchange('height', 'weight')
    def onchange_height_weight(self):
        res = {}
        if self.height <= 0 or self.weight <= 0:
            raise ValidationError(
                'Chiều cao và cân nặng phải phải lớn hơn 0')
        if self.height:
            self.bmi = self.weight / ((self.height / 100) ** 2)
        else:
            self.bmi = 0
        return res

    def _search_has_processing_lab(self, operator, value):
        current_institution = self.env['sh.medical.health.center'].search([('his_company', '=', self.env.companies.ids[0])], limit=1)
        processing_labtest = self.env['sh.medical.lab.test'].search([('institution', '=', current_institution.id), ('state', '!=', 'Completed')])
        walkin_ids = processing_labtest.mapped('walkin.id')
        if (operator == '=' and value is True) or (operator == '!=' and value is False):
            return [('id', 'in', walkin_ids)]
        elif (operator == '=' and value is False) or (operator == '!=' and value is True):
            return [('id', 'not in', walkin_ids)]
        else:
            return []

    @api.depends('date', 'service_room')
    def _compute_date_to_index(self):
        for record in self:
            # Todo: Update thêm điều kiện : if record.index_by_day:
                start = record.date.strftime("%Y-%m-%d 00:00:00")
                end = record.date.strftime("%Y-%m-%d 23:59:59")
                data = self.env['sh.medical.appointment.register.walkin'].search(
                    [('date', '>=', start), ('date', '<=', end), ('service_room', '=', record.service_room.id)],
                    order="date")
                if len(data) > 0:
                    list_date = data.mapped('date')
                    list_date.append(record.date)
                    list_date.sort()
                    record.index_by_day = list_date.index(record.date) + 1
                else:
                    record.index_by_day = 1

    @api.depends('reception_id.reception_date')
    def _compute_date(self):
        for record in self:
            if record.reception_id.reception_date:
                record.date = datetime.datetime.strptime(
                    record.reception_id.reception_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S") + timedelta(
                    minutes=5) or fields.Datetime.now()
            else:
                record.date = fields.Datetime.now()

    @api.depends('service', 'lab_test_ids', 'imaging_ids')
    def _compute_service_case(self):
        for record in self:
            # có chọn dịch vụ
            if record.service:
                record.compute_service = self.env.ref('shealth_all_in_one.sh_product_service_kb01').product_id + \
                                         record.lab_test_ids.filtered(
                                             lambda m: m.state in ['Test In Progress', 'Completed']). \
                                             mapped('test_type.product_id') + \
                                         record.imaging_ids.filtered(
                                             lambda m: m.state in ['Test In Progress', 'Completed']). \
                                             mapped('test_type.product_id') + \
                                         record.service.mapped('product_id')

    compute_service = fields.Many2many('product.product', compute=_compute_service_case)

    # @api.depends('patient_log')
    # def _compute_patient_log(self):
    #     for wk in self:
    #         if wk.patient_log:
    #             for log in wk.patient_log:
    #                 if not log.date_out:
    #                     wk.department_current = log.department
    #
    # department_current = fields.Many2one('sh.medical.health.center.ward', string='Department Current',
    #                                      help="Department Current", compute=_compute_patient_log, store="True")


    @api.depends('booking_id.price_list_id.item_ids')
    def _compute_pricelist_products(self):
        for record in self:
            if record.state in ['Scheduled', 'InProgress']:
                record.pricelist_products = record.booking_id.price_list_id.item_ids.product_id
            else:
                record.pricelist_products = False

    pricelist_products = fields.Many2many('product.product', 'Pricelist products', compute='_compute_pricelist_products')


    _sql_constraints = [
        ('full_name_uniq', 'unique (name,institution)', 'The Queue Number must be unique')
    ]

    # tong hop vat tu da dung trong phieu
    # @api.one
    # @api.depends('lab_test_ids', 'imaging_ids', 'surgeries_ids')
    # def _compute_materials(self):
    #     # self.update_walkin_material()
    #     self.material_ids = False
    #
    #     print(self.lab_test_ids)
    #     mats = []
    #     seq_mat = 0
    #     for lab in self.lab_test_ids:
    #         for lab_mats in lab.lab_test_material_ids:
    #             seq_mat += 1
    #             mats.append((0, 0, {'product_id': lab_mats.product_id.id,
    #                                 'sequence': seq_mat,
    #                                 'quantity': lab_mats.quantity,
    #                                 'institution': lab.institution.id,
    #                                 'department': lab.department.id,
    #                                 'uom_id': lab_mats.uom_id.id,
    #                                 'is_readonly': True,
    #                                 'walkin': self.id,
    #                                 'note': 'Labtest',
    #                                 'interner_note': 'Labtest'}))
    #
    #     for img in self.imaging_ids:
    #         for img_mats in img.imaging_material_ids:
    #             seq_mat += 1
    #             mats.append((0, 0, {'product_id': img_mats.product_id.id,
    #                                 'sequence': seq_mat,
    #                                 'quantity': img_mats.quantity,
    #                                 'institution': img.institution.id,
    #                                 'department': img.department.id,
    #                                 'uom_id': img_mats.uom_id.id,
    #                                 'is_readonly': True,
    #                                 'walkin': self.id,
    #                                 'note': 'Imaging',
    #                                 'interner_note': 'Imaging'}))
    #
    #     for sur in self.surgeries_ids:
    #         for sur_mats in sur.supplies:
    #             seq_mat += 1
    #             mats.append((0, 0, {'product_id': sur_mats.supply.id,
    #                                 'sequence': seq_mat,
    #                                 'quantity': sur_mats.qty_used,
    #                                 'institution': sur.institution.id,
    #                                 'department': sur.department.id,
    #                                 'uom_id': sur_mats.uom_id.id,
    #                                 'is_readonly': True,
    #                                 'walkin': self.id,
    #                                 'note': 'Surgery',
    #                                 'interner_note': 'Surgery'}))
    #
    #     print(mats)
    #     self.material_ids = mats

    # @api.one
    # @api.depends('lab_test_ids','imaging_ids','surgeries_ids','specialty_ids','state')
    # def sum_money_spent(self):
    #     ms = 0
    #     # ghi nhan tien dich vu
    #     if self.state == 'Completed':
    #         ms = self.service.list_price
    #     # elif self.surgery_done_count == self.surgery_count and self.surgery_count > 0:
    #     #     ms = self.service.list_price
    #     # elif self.specialty_done_count == self.specialty_count and self.specialty_count > 0:
    #     #     ms = self.service.list_price
    #     else:
    #         for lab in self.lab_test_ids:
    #             if lab.state == 'Test In Progress' or lab.state == 'Completed':
    #                 ms += lab.test_type.list_price
    #
    #         for img in self.imaging_ids:
    #             if img.state == 'Test In Progress' or img.state == 'Completed':
    #                 ms += img.test_type.list_price
    #
    #     self.money_spent = ms

    # view labtest by walkin

    def view_labtest_by_walkin(self):
        return {
            'name': _('View List LabTest by Walkin'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_lab_test_tree').id,
            'res_model': 'sh.medical.lab.test',  # model want to display
            'target': 'new',  # if you want popup
            'domain': [('walkin', '=', self.id)],
        }

    #  TRẢ KẾT QUẢ XN

    def return_result_labtest_by_walkin(self):
        self.env['ir.actions.actions'].clear_caches()

        return {
            'name': _('TRẢ KẾT QUẢ XN'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.walkin_labtest_result_view_form').id,
            'res_model': 'walkin.labtest.result',  # model want to display
            'target': 'new',  # if you want popup
        }

    # view imaging by walkin

    def view_imaging_by_walkin(self):
        return {
            'name': _('View List Imaging by Walkin'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_imaging_test_tree').id,
            'res_model': 'sh.medical.imaging',  # model want to display
            'target': 'new',  # if you want popup
            'domain': [('walkin', '=', self.id)],
        }

    # view surgery by walkin

    def view_surgery_by_walkin(self):
        return {
            'name': _('View List Surgery by Walkin'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_surgery_tree').id,
            'res_model': 'sh.medical.surgery',  # model want to display
            'target': 'new',  # if you want popup
            'domain': [('walkin', '=', self.id)],
        }

    # view specialty by walkin

    def view_specialty_by_walkin(self):
        return {
            'name': _('Xem Phiếu Chuyên khoa của Phiếu khám'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_specialty_tree').id,
            'res_model': 'sh.medical.specialty',  # model want to display
            'target': 'new',  # if you want popup
            'domain': [('walkin', '=', self.id)],
        }

    def view_walkin_material(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Materials of Walkin Details'),
                'res_model': 'sh.medical.walkin.material',
                # 'target': 'fullscreen',
                'view_mode': 'tree',
                'domain': [('walkin', '=', self.id)],
                'context': {'search_default_group_department': True},
                'views': [[self.env.ref('shealth_all_in_one.sh_medical_materials_of_walkin_tree').id, 'tree']],
                }

    def action_view_walkin(self):
        domain = ['|', ('company_id', 'in', self.env.companies.ids), ('company2_id', 'in', self.env.companies.ids)]
        room_type_dict = {'shealth_all_in_one.group_sh_medical_physician_surgery': 'Surgery',
                          'shealth_all_in_one.group_sh_medical_physician_odontology': 'Odontology',
                          'shealth_all_in_one.group_sh_medical_physician_spa': 'Spa',
                          'shealth_all_in_one.group_sh_medical_physician_laser': 'Laser'}

        room_types = []
        for grp, rt in room_type_dict.items():
            if self.env.user.has_group(grp):
                room_types.append(rt)
        if room_types:
            domain = [('room_type', 'in', room_types)] + domain
        return {'type': 'ir.actions.act_window',
                'name': _('Phiếu khám bệnh'),
                'res_model': 'sh.medical.appointment.register.walkin',
                # 'target': 'fullscreen',
                'view_mode': 'tree,kanban,calendar,form',
                'domain': domain,
                'context': {'search_default_group_date': True},
                }


    def add_evaluations(self):
        institution = self.env['sh.medical.health.center'].sudo().search(
            [('his_company', '=', self.env.company.id)], limit=1)

        # print(institution.name)
        # room = self.env['sh.medical.health.center.ot']

        res = self.env['sh.medical.evaluation'].create({
            'walkin': self.env.context.get('default_walkin'),
            'patient':  self.env.context.get('default_patient'),
            # 'doctor':  self.env.context.get('default_doctor'),
            'evaluation_start_date': datetime.date.today(),
            'services': self.env.context.get('default_services'),
            'institution': institution.id if institution else self.env.context.get('default_institution'),
            'room': institution.id if institution else self.env.context.get('default_institution'),
        })

        # res.write({'chief_complaint': 'Tái khám: %s' % ','.join(res.services.mapped('name')),'ward': res.walkin.service_room.related_department.id})
        if res.walkin.service_room.related_department:
            ward = res.walkin.service_room.related_department

            rooms = self.env['sh.medical.health.center.ot'].search([('department', '=', ward.id)])
            if ward.type == 'Surgery':
                rooms = rooms.filtered(lambda r: r.room_type == 'Examination')
            if rooms:
                room = rooms[0]
                res.write({'ward': ward.id, 'room': room.id})
            else:
                res.write({'ward': ward.id})
        return {
            'name': _('Chi tiết phiếu tái khám bệnh nhân'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_evaluation_view').id,
            'res_model': 'sh.medical.evaluation',  # model want to display
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': res.id
        }

    # ham dem xet nghiem
    @api.depends('lab_test_ids')
    def count_lab_test(self):
        current_institution = self.env['sh.medical.health.center'].search([('his_company', '=', self.env.companies.ids[0])], limit=1)
        for record in self:
            all_labtest = record.lab_test_ids
            labtest_done = record.lab_test_ids.filtered(lambda s: s.state == 'Completed')
            record.lab_test_count = len(all_labtest)
            record.lab_test_done_count = len(labtest_done)
            # record.has_lab_result = True if record.lab_test_done_count > 0 else False
            record.has_processing_lab = True if (len(all_labtest.filtered(lambda l: l.institution == current_institution)) - len(labtest_done.filtered(lambda l: l.institution == current_institution))) > 0 else False
            # record.has_processing_lab = True if record.lab_test_count - record.lab_test_done_count else False

    # ham dem cdha
    @api.depends('imaging_ids')
    def count_img_test(self):
        for record in self:
            record.img_test_count = len(record.imaging_ids.filtered(lambda s: s.state != 'Cancelled'))
            record.img_test_done_count = len(record.imaging_ids.filtered(lambda s: s.state == 'Completed'))
            record.has_img_result = True if record.img_test_count - record.img_test_done_count == 0 else False

    # ham dem pttt
    @api.depends('surgeries_ids.state')
    def count_surgery(self):
        for record in self:
            record.surgery_count = len(record.surgeries_ids.filtered(lambda s: s.state != 'Cancelled'))
            record.surgery_done_count = len(record.surgeries_ids.filtered(lambda s: s.state in ['Done', 'Signed']))

    # ham dem specialty
    @api.depends('specialty_ids.state')
    def count_specialty(self):
        for record in self:
            record.specialty_count = len(record.specialty_ids.filtered(lambda s: s.state != 'Cancelled'))
            record.specialty_done_count = len(record.specialty_ids.filtered(lambda s: s.state == 'Done'))

    @api.onchange('institution')
    def _onchange_institution(self):
        # set khoa mac dinh la khoa kham benh cua co so y te
        if self.institution:
            exam_dep = self.env['sh.medical.health.center.ward'].search(
                [('institution', '=', self.institution.id), ('type', '=', 'Examination')], limit=1)
            self.department = exam_dep
            self.service_room = ''

    # @api.onchange('pathology')
    # def _onchange_pathology(self):
    #     if self.service:#xoa nhung dich vu ko cung nhom benh
    #         for ser in self.service:
    #             if ser.pathology.id != self.pathology.id:
    #                 self.service = [(2, ser.id)]

    @api.onchange('doctor')
    def _onchange_doctor(self):
        if self.doctor:  # ghi nhận bac si yêu cau o cac phieu can lam sang
            for labtest in self.lab_test_ids:
                labtest.requestor = self.doctor

            for imaging in self.imaging_ids:
                imaging.requestor = self.doctor

            for surgery in self.surgeries_ids:
                surgery.surgeon = self.doctor

            for specialty in self.specialty_ids:
                specialty.physician = self.doctor

    # CASE ĐỔI DỊCH VỤ TRONG PHIẾU KHÁM
    def write(self, vals):
        res = super(SHealthAppointmentWalkin, self).write(vals)
        if vals.get('service') or vals.get('uom_price'):
            for record in self:
                service_vals = vals.get('service')
                uom_price = vals.get('uom_price') or record.uom_price
                medical_services = self.env['sh.medical.health.center.service'].browse(service_vals[0][2]) if service_vals else record.service
                product_ids = medical_services.mapped('product_id.id')

                added_products = [s for s in product_ids if
                                  s not in record.sale_order_id.order_line.mapped('product_id.id')]
                if vals.get('service'):
                    # SỬA SẢN PHẨM Ở ORDER LINE TRONG SO
                    for line in record.sale_order_id.order_line:
                        if line.product_id.id not in product_ids:
                            # line.crm_line_id.cancel = True
                            #nếu xóa dịch vụ trong phiếu khám thì đưa trạng thái dòng crm line về new - Được sử dụng
                            line.crm_line_id.stage = 'new'
                            line.unlink()
                    # CÁC DỊCH VỤ MỚI ĐƯỢC ADD THÊM Ở PHIẾU KHÁM SẼ SỬ DỤNG BẢNG GIÁ NIÊM YẾT CỦA THƯƠNG HIỆU
                    price_list = self.env['product.pricelist']
                    if record.sale_order_id.pricelist_id.type == 'service':
                        price_list += record.sale_order_id.pricelist_id
                    else:
                        price_list += self.env['product.pricelist'].search([('brand_id', '=', record.sale_order_id.brand_id.id), ('type', '=', 'service')], limit=1)
                    for product_id in added_products:
                        product = self.env['product.product'].browse(product_id)
                        product_price = product.lst_price
                        item_price = self.env['product.pricelist.item'].search(
                            [('pricelist_id', '=', price_list.id), ('product_id', '=', product_id)])
                        if item_price:
                            product_price = item_price.fixed_price
                        record.sale_order_id.document_related = record.name
                        self.env['sale.order.line'].create({'order_id': record.sale_order_id.id,
                                                            'product_id': product_id,
                                                            'product_uom': product.uom_id.id,
                                                            'company_id': record.institution.his_company.id,
                                                            'price_unit': product_price,
                                                            'product_uom_qty': 1,
                                                            })

                # check số lượng làm 1 lần phải nhỏ hơn số lượng bên booking
                #nếu là phiếu khám nha khoa thì mới check trường này
                # if self.room_type == 'Odontology':
                    # crm_line_qty = sum(record.booking_id.crm_line_ids.filtered(
                    #     lambda l: (l.product_id.id in product_ids) and (l.stage in ('new', 'processing'))).mapped(
                    #     'uom_price'))
                    # if uom_price > crm_line_qty:
                    #     raise ValidationError(_('Số lượng phải ít hơn số lượng từ Booking.'))
                    # crm_line_qty = sum(record.booking_id.crm_line_ids.filtered(
                    #     lambda l: (l.product_id.id in product_ids) and (l.stage in ('new', 'processing'))).mapped(
                    #     'uom_price'))

                #check dịch vụ đổi trong phiếu khám so với phiếu chuyên khoa/pttt --- KO Ở TRẠNG THÁI NHÁP
                specialties = record.specialty_ids
                surgeries = record.surgeries_ids
                inpatients = record.inpatient_ids
                #pttt
                for surgery in surgeries.filtered(lambda s: s.state not in ['Draft']).mapped('services').ids:
                    if surgery not in record.service.ids:
                        raise ValidationError('Dịch vụ đã được xác nhận tại phiếu PTTT nên bạn không thể đổi dịch vụ được!')

                # lưu bệnh nhân
                for inpatient in inpatients.filtered(lambda s: s.state not in ['Draft']).mapped('services').ids:
                    if inpatient not in record.service.ids:
                        raise ValidationError(
                            'Dịch vụ đã được xác nhận tại phiếu lưu bệnh nhân nên bạn không thể đổi dịch vụ được!')

                #chuyên khoa
                for specialty in specialties.filtered(lambda s: s.state not in ['Draft']).mapped('services').ids:
                    if specialty not in record.service.ids:
                        raise ValidationError(
                            'Dịch vụ đã được xác nhận tại phiếu Chuyên khoa nên bạn không thể đổi dịch vụ được!')

                # check dịch vụ đổi trong phiếu khám so với phiếu chuyên khoa/pttt --- TRẠNG THÁI NHÁP
                # pttt
                for surgery_draft in surgeries.filtered(lambda s: s.state in ['Draft']).mapped('services').ids:
                    if surgery_draft not in record.service.ids:
                        record.surgeries_ids.write({'services': [(3, surgery_draft)]})

                # lưu bệnh nhân
                for inpatient_draft in inpatients.filtered(lambda s: s.state in ['Draft']).mapped('services').ids:
                    if inpatient_draft not in record.service.ids:
                        record.inpatient_ids.write({'services': [(3, inpatient_draft)]})

                # chuyên khoa
                for specialty_draft in specialties.filtered(lambda s: s.state in ['Draft']).mapped('services').ids:
                    if specialty_draft not in record.service.ids:
                        record.specialty_ids.write({'services': [(3, specialty_draft)]})

                # các thanh toán của phiếu khám
                # check số tiền đã thu và số tiền trong SO đã khớp chưa

                # nếu trang thái phiếu là đang thực hiện thì back về trạng thái chờ thu tiền, nếu ko (dạng Nháp) thì giữ nguyên trạng thái, chỉ chuyển trạng thái khi click Yêu cầu thu phí
                total_so = record.sale_order_id.amount_total
                total_payment_walkin = record.sale_order_id.amount_remain
                amount_owed = record.sudo().sale_order_id.amount_owed  # Số tiền khách được duyệt nợ

                if record.sudo().sale_order_id.check_order_missing_money():  # thiếu tiền
                    if record.state == 'InProgress':
                        record.sudo().create_draft_payment()

                else:  # đã đóng đủ tiền => chuyển trạng
                    if(record.sale_order_id.state in ['draft','sent']):
                        record.set_to_progress()

        # nếu thay đổi ngày khám thì sửa lại cả ngày ở phiếu đón tiếp
        if vals.get('date'):
            for record in self:
                date_vals = vals.get('date')
                record.reception_id.reception_date = datetime.datetime.strptime(
                    date_vals, "%Y-%m-%d %H:%M:%S") - timedelta(
                    minutes=5) or fields.Datetime.now()

                # record.sale_order_id.date_order = datetime.datetime.strptime(
                #     date_vals, "%Y-%m-%d %H:%M:%S") or fields.Datetime.now()

        # nếu thay đổi ngày làm dịch vụ thì sửa lại ngày ở SO liên quan
        if vals.get('service_date'):
            for record in self:
                service_date_vals = vals.get('service_date')

                record.sale_order_id.date_order = datetime.datetime.strptime(
                    service_date_vals, "%Y-%m-%d %H:%M:%S") or fields.Datetime.now()

        return res

    @api.onchange('service')
    def _onchange_services_case(self):
        if self.service:
            walkin_flag_surgery = False
            if self.service_room.related_department.type == 'Surgery':
                walkin_flag_surgery = True

            self.flag_surgery = walkin_flag_surgery
            self.pathology = self.service[0].pathology.id

            if not self.department and self.service_room:
                self.department = self.service_room.department

                # Nếu phiếu đã thu tiền
                # if self.state not in ['Scheduled', 'WaitPayment', 'Payment']:
                #     payment_detail = self.env['account.payment'].browse(self.payment_ids[0].id or False)
                #     # đã có phiếu thu
                #     if len(payment_detail) > 0:
                #         service_name = ''
                #         total = 0
                #         for ser in self.service:
                #             total += ser.list_price
                #             service_name += ser.name + ";"
                #
                #         payment_detail.write({
                #             'amount': total,
                #             'note': "Thu phí dịch vụ: " + service_name,
                #             'text_total': num2words_vnm(int(total)) + " đồng",
                #         })

    #     marterial_wakin = []
    #     id_marterial_wakin = {}
    #
    #     # START - xoa nhung phieu dang nhap khi change service
    #     if self.lab_test_ids:
    #         for lt_id in self.lab_test_ids:
    #             if lt_id.state == 'Draft':
    #                 self.lab_test_ids = [(2,lt_id.id)]
    #
    #     lab_test_wakin = []
    #     id_lab_test_wakin = self.lab_test_ids.mapped('test_type').ids
    #
    #     if self.imaging_ids:
    #         for img_id in self.imaging_ids:
    #             if img_id.state == 'Draft':
    #                 self.imaging_ids = [(2, img_id.id)]
    #
    #     img_test_wakin = []
    #     id_img_test_wakin = self.imaging_ids.mapped('test_type').ids
    #
    #     if self.surgeries_ids:
    #         for sur_id in self.surgeries_ids:
    #             if sur_id.state == 'Draft':
    #                 self.surgeries_ids = [(2, sur_id.id)]
    #             # else:
    #             #     raise ValidationError(_('You can not remove surgery not in Draft!'))
    #
    #     surgery_wakin = []
    #     id_surgery_test_wakin = self.surgeries_ids.mapped('services').ids
    #
    #     if self.specialty_ids:
    #         for spec_id in self.specialty_ids:
    #             if spec_id.state == 'Draft':
    #                 self.specialty_ids = [(2, spec_id.id)]
    #             # else:
    #             #     raise ValidationError(_('You can not remove service not in Draft!'))
    #     specialty_wakin = []
    #     id_specialty_test_wakin = self.specialty_ids.mapped('services').ids
    #
    #     # if self.prescription_ids:
    #     #     for pres_id in self.prescription_ids:
    #     #         if pres_id.state == 'Draft':
    #     #             self.prescription_ids = [(2, pres_id.id)]
    #     # prescription_wakin = []
    #
    #     # END - xoa nhung phieu dang nhap khi change service
    #
    #     #TAO CÁC PHIEU XN, CĐHA, PTTT, CK NẾU CÓ
    #     seq_mat = 0
    #     for ser in self.service:
    #         # add vat tu tieu hao tong - ban dau
    #         # for mats in ser.material_ids:
    #         #     # if mats.product_id.id not in id_marterial_wakin: #chua co thi tao moi vtth
    #         #     #     id_marterial_wakin.append(mats.product_id.id)
    #         #     walkin_dict_key = str(mats.product_id.id) + '-' + str(mats.department.id)
    #         #     if not id_marterial_wakin.get(walkin_dict_key):
    #         #         seq_mat += 1
    #         #         id_marterial_wakin[walkin_dict_key] = seq_mat
    #         #         marterial_wakin.append((0, 0, {'product_id': mats.product_id.id,
    #         #                                      'sequence': seq_mat,
    #         #                                      'quantity': mats.quantity,
    #         #                                      'institution': mats.institution.id,
    #         #                                      'department': mats.department.id,
    #         #                                      'uom_id': mats.uom_id.id,
    #         #                                      'is_readonly': True,
    #         #                                      'note': mats.note,
    #         #                                      'interner_note': mats.note}))
    #         #     #co vtth roi thi lay so luong lon nhat
    #         #     elif mats.quantity > marterial_wakin[id_marterial_wakin[walkin_dict_key]-1][2]['quantity']:
    #         #         marterial_wakin[id_marterial_wakin[walkin_dict_key]-1][2]['quantity'] = mats.quantity
    #             # else:
    #
    #         # add lab test
    #         for lab in ser.lab_type_ids:
    #             if lab.id not in id_lab_test_wakin:
    #                 lab_department = self.env['sh.medical.health.center.ward'].search(
    #                     [('institution', '=', self.institution.id), ('type', '=', 'Laboratory')], limit=1)
    #
    #                 id_lab_test_wakin.append(lab.id) # co roi se khong add thêm nữa
    #                 lab_test_wakin.append((0, 0, {
    #                                             'institution': self.institution.id,
    #                                            'department': lab_department,
    #                                            'test_type': lab.id,
    #                                            'has_child': lab.has_child,
    #                                            'normal_range': lab.normal_range,
    #                                            'patient': self.patient.id,
    #                                            'date_requested': datetime.datetime.now(),
    #                                            'requestor':self.doctor.id,
    #                                            # 'pathologist':self.doctor.id,
    #                                            'lab_test_material_ids':[],
    #                                            'lab_test_criteria':[],
    #                                            'walkin': self._origin.id,
    #                                            'state': 'Draft'}))
    #
    #         # add imaging test
    #         for img in ser.imaging_type_ids:
    #             if img.id not in id_img_test_wakin:
    #                 img_department = self.env['sh.medical.health.center.ward'].search(
    #                     [('institution', '=', self.institution.id), ('type', '=', 'Imaging')], limit=1)
    #
    #                 id_img_test_wakin.append(img.id) # co roi se khong add thêm nữa
    #                 img_test_wakin.append((0, 0, {
    #                                           'institution': self.institution.id,
    #                                           'department': img_department,
    #                                           'test_type': img.id,
    #                                           'patient': self.patient.id,
    #                                           'date_requested': datetime.datetime.now(),
    #                                           'requestor': self.doctor.id,
    #                                           # 'pathologist': self.doctor.id,
    #                                           'imaging_material_ids': [],
    #                                           'walkin': self._origin.id,
    #                                           'state': 'Draft'}))
    #
    #         # material_of_walkin = res.walkin.material_ids
    #         # sg_supply_data = []
    #         # for sg in material_of_walkin:
    #         #     if sg.note == 'Surgery':
    #         #         sg_supply_data.append((0, 0, {'note': sg.note,
    #         #                                'supply': sg.product_id.id,
    #         #                                'qty': sg.quantity,
    #         #                                'qty_use': sg.uom_id.id,
    #         #                                        'uom_id': sg.uom_id.id}))
    #
    #         #add surgeries (neu co)
    #         if ser.is_surgeries:
    #             sur_department = ser.service_department.filtered(lambda s: s.institution == self.institution and s.type == 'Surgery')
    #             sur_room = ser.service_room.filtered(lambda s: s.institution == self.institution)
    #             if sur_room:
    #                 sur_room = sur_room[0]
    #
    #             if ser.id not in id_surgery_test_wakin:
    #                 surgery_wakin.append((0, 0, {
    #                                           'institution': self.institution.id,
    #                                           'department': sur_department,
    #                                           'operating_room': sur_room,
    #                                           'services': ser,
    #                                           'pathology': self.pathology.id,
    #                                           'patient': self.patient.id,
    #                                           'surgery_date': datetime.datetime.now(),
    #                                           'surgeon': self.doctor.id,
    #                                           'walkin': self._origin.id,
    #                                           'state': 'Draft'}))
    #         else:
    #             spec_department = ser.service_department.filtered(
    #                 lambda s: s.institution == self.institution and s.type == 'Specialty')
    #             spec_room = ser.service_room.filtered(lambda s: s.institution == self.institution)
    #             if spec_room:
    #                 spec_room = spec_room[0]
    #             if ser.id not in id_specialty_test_wakin:
    #                 specialty_wakin.append((0, 0, {
    #                                           'institution': self.institution.id,
    #                                           'department': spec_department,
    #                                           'perform_room': spec_room,
    #                                           'services': ser,
    #                                           'pathology': self.pathology.id,
    #                                           'patient': self.patient.id,
    #                                           'services_date': datetime.datetime.now(),
    #                                           'physician': self.doctor.id,
    #                                           'walkin': self._origin.id,
    #                                           'state': 'Draft'}))
    #         #nếu dịch vụ có đơn thuốc kèm theo
    #         # if ser.prescription_ids:
    #         #     # location_id = self.env['stock.location'].search()
    #         #     prescription_wakin.append((0, 0, {
    #         #         'info': ser.name,
    #         #         'patient': self.patient.id,
    #         #         'date': datetime.datetime.now(),
    #         #         'doctor': self.doctor.id,
    #         #         'walkin': self._origin.id,
    #         #         'state': 'Draft'}))
    #         #
    #         # print(prescription_wakin)
    #
    #     # set nguoi chi dinh khi thay doi dich vu
    #     self.update({'lab_test_ids': lab_test_wakin,'imaging_ids': img_test_wakin,'surgeries_ids': surgery_wakin,'specialty_ids':specialty_wakin})
    #     # self.update({'material_ids': marterial_wakin,'lab_test_ids': lab_test_wakin,'imaging_ids': img_test_wakin,'surgeries_ids': surgery_wakin,'taskmaster': self.env.user.id})

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code(
            'sh.medical.appointment.register.walkin.%s' % vals['institution'])
        if not sequence:
            raise ValidationError(_('Định danh phiếu Khám của Cơ sở y tế này đang không tồn tại!'))
        vals['name'] = sequence
        res = super(SHealthAppointmentWalkin, self).create(vals)

        # log access patient
        # vals_log = {'walkin': res.id,
        #             'patient': res.patient.id,
        #             'department': res.department.id,
        #             'date_in': res.date}
        # self.env['sh.medical.patient.log'].create(vals_log)
        return res

    @api.onchange('patient')
    def onchange_patient(self):
        if self.patient:
            self.dob = self.patient.birth_date
            self.sex = self.patient.gender
            self.marital_status = self.patient.marital_status
            self.blood_type = self.patient.blood_type
            self.rh = self.patient.rh

    def _default_account(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.default_credit_account_id.id

    #
    # def action_walkin_invoice_create(self):
    #     invoice_obj = self.env["account.invoice"]
    #     invoice_line_obj = self.env["account.invoice.line"]
    #     inv_ids = []
    #
    #     for acc in self:
    #         # Create Invoice
    #         if acc.doctor:
    #             curr_invoice = {
    #                 'partner_id': acc.patient.partner_id.id,
    #                 'account_id': acc.patient.partner_id.property_account_receivable_id.id,
    #                 'patient': acc.patient.id,
    #                 'state': 'draft',
    #                 'type':'out_invoice',
    #                 'date_invoice': acc.date.date(),
    #                 'origin': "Walkin # : " + acc.name,
    #             }
    #
    #             inv_ids = invoice_obj.create(curr_invoice)
    #
    #             if inv_ids:
    #                 inv_id = inv_ids.id
    #                 prd_account_id = self._default_account()
    #
    #                 # Create Invoice line
    #                 curr_invoice_line = {
    #                     'name':"Consultancy invoice for " + acc.name,
    #                     'price_unit': acc.doctor.consultancy_price,
    #                     'quantity': 1,
    #                     'account_id': prd_account_id,
    #                     'invoice_id': inv_id,
    #                 }
    #
    #                 inv_line_ids = invoice_line_obj.create(curr_invoice_line)
    #             self.write({'state': 'Invoiced'})
    #
    #         else:
    #             raise UserError(_('Configuration error!\nCould not find any physician to create the invoice !'))
    #
    #     return {
    #             'domain': "[('id','=', " + str(inv_id) + ")]",
    #             'name': 'Walkin Invoice',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             'res_model': 'account.invoice',
    #             'type': 'ir.actions.act_window'
    #     }

    #CẬP NHẬT THÔNG TIN VT CỦA TOÀN BỘ PHIẾU KHÁM
    def update_walkin_material(self, mats_types=None):
        # Chỉ xóa những vật tư theo loại được truyền vào, nếu không có tham số truyền vào mới xóa hết
        self = self.sudo()  # cập nhật vật tư cho các case share company - người dùng không có quyền write pk
        if not mats_types:
            mats = [(2, mats_id) for mats_id in self.material_ids.ids]
        else:
            to_delete = self.material_ids.filtered(lambda m: m.note in mats_types)
            mats = [(2, mats_id) for mats_id in to_delete.ids]

        seq_mat = 0
        over = False
        evaluations = self.env['sh.medical.evaluation'].search([('walkin', '=', self.id)])
        if 'Inpatient' in mats_types or 'Evaluation' in mats_types:
            for evaluation in evaluations.filtered(lambda l: l.state in ['Completed']):
                for evaluation_mats in evaluation.supplies:
                    seq_mat += 1
                    if evaluation.evaluation_type == 'Inpatient Admission':  # nếu loại đánh giá là nhập viện thì lấy vật tư ở khoa hậu phẫu
                        dept = self.env['sh.medical.health.center.ward'].search(
                            [('institution', '=', self.institution.id), ('type', '=', 'Inpatient')], limit=1)
                        evaluation_dept = dept.id
                        evaluation_inst = self.institution.id
                        note = "Inpatient"
                    else:  # nếu là loại đánh giá khác thì trừ vtth ở khoa theo phiếu đánh giá
                        evaluation_dept = evaluation.ward.id
                        evaluation_inst = evaluation.institution.id
                        note = "Evaluation"
                    mats.append((0, 0, {'product_id': evaluation_mats.supply.id,
                                        'sequence': seq_mat,
                                        'init_quantity': evaluation_mats.qty,
                                        'quantity': evaluation_mats.qty_used,
                                        'institution': evaluation_inst,
                                        'department': evaluation_dept,
                                        'uom_id': evaluation_mats.uom_id.id,
                                        'is_readonly': True,
                                        'note': note,
                                        'date_out': evaluation.evaluation_end_date,
                                        'services': [(6, 0, evaluation.services.ids)],
                                        'location_id': evaluation_mats.sudo().location_id.id,
                                        'interner_note': evaluation_mats.notes,
                                        'ref_id': '%s,%s' % (evaluation._name, evaluation.id),
                                        'picking_id': evaluation_mats.picking_id.id}))
                    # over = True

                    if evaluation_mats.qty_used > evaluation_mats.qty:
                        over = True

        id_marterial_lab = {}
        if 'Labtest' in mats_types:
            for lab in self.lab_test_ids.filtered(lambda l: l.state in ['Completed']):
                for lab_mats in lab.lab_test_material_ids:
                    # chuyen doi ve đon vi goc cua medicament
                    # lab_dict_key = str(lab_mats.product_id.id) + '-' + str(lab.department.id) + '-' + 'Labtest' + '-' + str(
                    #     lab.sudo().perform_room.location_supply_stock.id)
                    lab_qty_line = lab_mats.uom_id._compute_quantity(lab_mats.quantity, lab_mats.product_id.uom_id)
                    lab_init_qty_line = lab_mats.uom_id._compute_quantity(lab_mats.init_quantity,
                                                                          lab_mats.product_id.uom_id)

                    # chua co thi tao moi
                    # if not id_marterial_lab.get(lab_dict_key):
                    #     seq_mat += 1
                    #     id_marterial_lab[lab_dict_key] = seq_mat

                    mats.append((0, 0, {'product_id': lab_mats.product_id.id,
                                        'sequence': seq_mat,
                                        'init_quantity': lab_init_qty_line,
                                        'quantity': lab_qty_line,
                                        'institution': lab.institution.id,
                                        'department': lab.department.id,
                                        'uom_id': lab_mats.product_id.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Labtest',
                                        'date_out': lab.date_done,
                                        'services': [(6, 0, lab.walkin.service.ids)],
                                        'location_id': lab.sudo().perform_room.location_supply_stock.id,
                                        'interner_note': lab_mats.notes,
                                        'ref_id': '%s,%s' % (lab._name, lab.id),
                                        'picking_id': lab_mats.picking_id.id}))
                    # co vtth roi thi cộng dồn số yc ban đầu và số lượng sử dụng
                    # else:
                    #     mats[id_marterial_lab[lab_dict_key] - 1][2]['init_quantity'] += lab_init_qty_line
                    #     mats[id_marterial_lab[lab_dict_key] - 1][2]['quantity'] += lab_qty_line

                    # if mats[id_marterial_lab[lab_dict_key] - 1][2]['quantity'] > \
                    #         mats[id_marterial_lab[lab_dict_key] - 1][2]['init_quantity']:
                    #     over = True

                    if lab_qty_line > lab_init_qty_line:
                        over = True

        id_marterial_img = {}
        if 'Imaging' in mats_types:
            for img in self.imaging_ids.filtered(lambda l: l.state in ['Completed']):
                for img_mats in img.imaging_material_ids:
                    # chuyen doi ve đon vi goc cua medicament
                    # img_dict_key = str(img_mats.product_id.id) + '-' + str(img.department.id) + '-' + 'Imaging' + '-' + str(
                    #     img.sudo().perform_room.location_supply_stock.id)
                    img_qty_line = img_mats.uom_id._compute_quantity(img_mats.quantity, img_mats.product_id.uom_id)
                    img_init_qty_line = img_mats.uom_id._compute_quantity(img_mats.init_quantity,
                                                                          img_mats.product_id.uom_id)
                    # chua co thi tao moi
                    # if not id_marterial_img.get(img_dict_key):
                    #     seq_mat += 1
                    #     id_marterial_img[img_dict_key] = seq_mat
                    mats.append((0, 0, {'product_id': img_mats.product_id.id,
                                        'sequence': seq_mat,
                                        'init_quantity': img_init_qty_line,
                                        'quantity': img_qty_line,
                                        'institution': img.institution.id,
                                        'department': img.department.id,
                                        'uom_id': img_mats.product_id.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Imaging',
                                        'date_out': img.date_done,
                                        'services': [(6, 0, img.walkin.service.ids)],
                                        'location_id': img.sudo().perform_room.location_supply_stock.id,
                                        'interner_note': img_mats.notes,
                                        'ref_id': '%s,%s' % (img._name, img.id),
                                        'picking_id': img_mats.picking_id.id}))

                    # co vtth roi thi cộng dồn số yc ban đầu và số lượng sử dụng
                    # else:
                    #     mats[id_marterial_img[img_dict_key] - 1][2]['init_quantity'] += img_init_qty_line
                    #     mats[id_marterial_img[img_dict_key] - 1][2]['quantity'] += img_qty_line
                    #
                    # if mats[id_marterial_img[img_dict_key] - 1][2]['quantity'] > \
                    #         mats[id_marterial_img[img_dict_key] - 1][2]['init_quantity']:
                    #     over = True

                    if img_qty_line > img_init_qty_line:
                        over = True

        id_marterial_sur = {}
        if 'Surgery' in mats_types:
            for sur in self.surgeries_ids.filtered(lambda l: l.state in ['Done', 'Signed']):
                for sur_mats in sur.supplies:
                    # chuyen doi ve đon vi goc cua medicament
                    # sur_dict_key = str(sur_mats.supply.id) + '-' + str(
                    #     sur.department.id) + '-' + 'Surgery' + '-' + str(
                    #     sur_mats.sudo().location_id)
                    sur_qty_line = sur_mats.uom_id._compute_quantity(sur_mats.qty_used, sur_mats.supply.uom_id)
                    sur_init_qty_line = sur_mats.uom_id._compute_quantity(sur_mats.qty,
                                                                          sur_mats.supply.uom_id)
                    # chua co thi tao moi
                    # if not id_marterial_sur.get(sur_dict_key):
                    #     seq_mat += 1
                    #     id_marterial_sur[sur_dict_key] = seq_mat
                    mats.append((0, 0, {'product_id': sur_mats.supply.id,
                                        'sequence': seq_mat,
                                        'init_quantity': sur_init_qty_line,
                                        'quantity': sur_qty_line,
                                        'institution': sur.institution.id,
                                        'department': sur.department.id,
                                        'uom_id': sur_mats.supply.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Surgery',
                                        'date_out': sur.surgery_end_date,
                                        'services': [(6, 0, sur_mats.services.ids)],
                                        'location_id': sur_mats.sudo().location_id.id,
                                        'interner_note': sur_mats.notes,
                                        'ref_id': '%s,%s' % (sur._name, sur.id),
                                        'picking_id': sur_mats.picking_id.id}))
                    # co vtth roi thi cộng dồn số yc ban đầu và số lượng sử dụng
                    # else:
                    #     mats[id_marterial_sur[sur_dict_key] - 1][2]['init_quantity'] += sur_init_qty_line
                    #     mats[id_marterial_sur[sur_dict_key] - 1][2]['quantity'] += sur_qty_line
                    #
                    # if mats[id_marterial_sur[sur_dict_key] - 1][2]['quantity'] > \
                    #         mats[id_marterial_sur[sur_dict_key] - 1][2]['init_quantity']:
                    #     over = True

                    if sur_qty_line > sur_init_qty_line:
                        over = True

        id_marterial_spec = {}
        if 'Specialty' in mats_types:
            for spec in self.specialty_ids.filtered(lambda l: l.state in ['Done']):
                for spec_mats in spec.supplies:
                    # chuyen doi ve đon vi goc cua medicament
                    # spec_dict_key = str(spec_mats.supply.id) + '-' + str(
                    #     spec.department.id) + '-' + 'Specialty' + '-' + str(
                    #     spec_mats.sudo().location_id)
                    spec_qty_line = spec_mats.uom_id._compute_quantity(spec_mats.qty_used, spec_mats.supply.uom_id)
                    spec_init_qty_line = spec_mats.uom_id._compute_quantity(spec_mats.qty,
                                                                            spec_mats.supply.uom_id)
                    # chua co thi tao moi
                    # if not id_marterial_spec.get(spec_dict_key):
                    #     seq_mat += 1
                    #     id_marterial_spec[spec_dict_key] = seq_mat
                    mats.append((0, 0, {'product_id': spec_mats.supply.id,
                                        'sequence': seq_mat,
                                        'init_quantity': spec_init_qty_line,
                                        'quantity': spec_qty_line,
                                        'institution': spec.institution.id,
                                        'department': spec.department.id,
                                        'uom_id': spec_mats.supply.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Specialty',
                                        'date_out': spec.services_end_date,
                                        'services': [(6, 0, spec_mats.services.ids)],
                                        'location_id': spec_mats.sudo().location_id.id,
                                        'interner_note': spec_mats.notes,
                                        'ref_id': '%s,%s' % (spec._name, spec.id),
                                        'picking_id': spec_mats.picking_id.id}))

                    # co vtth roi thi cộng dồn số yc ban đầu và số lượng sử dụng
                    # else:
                    #     mats[id_marterial_spec[spec_dict_key] - 1][2]['init_quantity'] += spec_init_qty_line
                    #     mats[id_marterial_spec[spec_dict_key] - 1][2]['quantity'] += spec_qty_line
                    #
                    # if mats[id_marterial_spec[spec_dict_key] - 1][2]['quantity'] > \
                    #         mats[id_marterial_spec[spec_dict_key] - 1][2]['init_quantity']:
                    #     over = True

                    if spec_qty_line > spec_init_qty_line:
                        over = True

        id_marterial_rouding = {}
        id_marterial_instruction = {}
        if 'Inpatient' in mats_types:
            for inpatient in self.inpatient_ids:
                # CHI TIET DIEU DUONG
                for rounding in inpatient.roundings.filtered(lambda l: l.state in ['Completed']):
                    # ghi nhận VTTH - CSHP
                    for rounding_mat in rounding.medicaments:
                        # TINH TOAN SO LUONG VAT TU BAN DAU
                        # for ser in self.service:
                        #     # add vat tu tieu hao tong - ban dau
                        #     for df_mats in ser.material_ids:
                        #         if df_mats.note == 'Inpatient':
                        #             walkin_dict_key = str(df_mats.product_id.id) + '-' + str(df_mats.note)
                        #             if not id_marterial_hp.get(walkin_dict_key):
                        #                 seq_mat += 1
                        #                 id_marterial_hp[walkin_dict_key] = seq_mat
                        #                 marterial_hp[str(df_mats.product_id.id)] = df_mats.quantity
                        #             #co vtth roi thi lay so luong lon nhat
                        #             elif df_mats.quantity > marterial_hp[str(df_mats.product_id.id)]:
                        #                 marterial_hp[str(df_mats.product_id.id)] = df_mats.quantity

                        # chuyen doi ve đon vi goc cua medicament
                        # rounding_dict_key = str(rounding_mat.medicine.id) + '-' + str(
                        #     inpatient.sudo().bed.room.location_supply_stock.id) + '-' + 'Inpatient' + '-' + str(
                        #     rounding_mat.sudo().location_id)
                        rounding_qty_line = rounding_mat.uom_id._compute_quantity(rounding_mat.qty,
                                                                                  rounding_mat.medicine.uom_id)

                        # chua co thi tao moi
                        # if not id_marterial_rouding.get(rounding_dict_key):
                        #     seq_mat += 1
                        #     id_marterial_rouding[rounding_dict_key] = seq_mat
                        mats.append((0, 0, {'product_id': rounding_mat.medicine.id,
                                            'sequence': seq_mat,
                                            'init_quantity': 0,
                                            'quantity': rounding_qty_line,
                                            'institution': self.institution.id,
                                            'department': inpatient.bed.ward.id,
                                            'uom_id': rounding_mat.medicine.uom_id.id,
                                            'is_readonly': True,
                                            'note': 'Inpatient',
                                            'date_out': rounding.evaluation_end_date,
                                            'services': [(6, 0, rounding_mat.services.ids)],
                                            'location_id': rounding_mat.sudo().location_id.id,
                                            'interner_note': rounding_mat.notes,
                                            'ref_id': '%s,%s' % (rounding._name, rounding.id),
                                            'picking_id': rounding_mat.picking_id.id}))
                        # co vtth roi thi cộng dồn số lượng sử dụng
                        # else:
                        #     mats[id_marterial_rouding[rounding_dict_key] - 1][2]['quantity'] += rounding_qty_line

                # Y LENH
                for instruction in inpatient.instructions.filtered(lambda l: l.state in ['Completed']):
                    for ylhp_mat in instruction.ins_medicaments:
                        # ghi nhận THUOC - CSHP
                        # instruction_dict_key = str(ylhp_mat.medicine.id) + '-' + str(
                        #     inpatient.sudo().bed.room.location_medicine_stock.id) + '-' + 'Inpatient' + '-' + str(
                        #     ylhp_mat.sudo().location_id)
                        instruction_qty_line = ylhp_mat.uom_id._compute_quantity(ylhp_mat.qty,
                                                                                 ylhp_mat.medicine.uom_id)
                        # chua co thi tao moi
                        # if not id_marterial_instruction.get(instruction_dict_key):
                        #     seq_mat += 1
                        #     id_marterial_instruction[instruction_dict_key] = seq_mat
                        mats.append((0, 0, {'product_id': ylhp_mat.medicine.id,
                                            'sequence': seq_mat,
                                            'init_quantity': 0,
                                            'quantity': instruction_qty_line,
                                            'institution': self.institution.id,
                                            'department': inpatient.bed.ward.id,
                                            'uom_id': ylhp_mat.medicine.uom_id.id,
                                            'is_readonly': True,
                                            'note': 'Inpatient',
                                            'date_out': instruction.evaluation_end_date,
                                            'services': [(6, 0, ylhp_mat.services.ids)],
                                            'location_id': ylhp_mat.sudo().location_id.id,
                                            'interner_note': ylhp_mat.notes,
                                            'ref_id': '%s,%s' % (instruction._name, instruction.id),
                                            'picking_id': ylhp_mat.picking_id.id}))
                        # co vtth roi thi cộng dồn số lượng sử dụng
                        # else:
                        #     mats[id_marterial_instruction[instruction_dict_key] - 1][2]['quantity'] += instruction_qty_line

        # VTTH THUOC CAP CHO BENH NHAN SAU DICH VU
        id_medicine_line = {}
        # check đã có thì cộng dồn
        if 'Medicine' in mats_types:
            for prescription in self.prescription_ids.filtered(lambda l: l.state in ['Đã xuất thuốc']):
                for medicine in prescription.prescription_line:
                    # med_dict_key = str(medicine.name.id) + '-' + 'Medicine'
                    med_init_qty_line = medicine.dose_unit_related._compute_quantity(medicine.init_qty,
                                                                                     medicine.name.uom_id)
                    med_qty_line = medicine.dose_unit_related._compute_quantity(medicine.qty,
                                                                                medicine.name.uom_id)

                    # if medicine.name.id not in id_medicine_line:
                    #     seq_mat += 1
                    #     id_medicine_line[med_dict_key] = seq_mat
                    mats.append((0, 0, {'product_id': medicine.name.id,
                                        'sequence': seq_mat,
                                        'init_quantity': med_init_qty_line,
                                        'quantity': med_qty_line,
                                        'institution': self.institution.id,
                                        'department': prescription.room_request.department.id or self.service_room.related_department.id or 1,
                                        'uom_id': medicine.name.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Medicine',
                                        'date_out': prescription.date_out,
                                        'services': [(6, 0, medicine.services.ids)],
                                        'location_id': medicine.sudo().location_id.id,
                                        'interner_note': medicine.note,
                                        'ref_id': '%s,%s' % (prescription._name, prescription.id),
                                        'picking_id': medicine.picking_id.id}))
                    # else:
                    #     mats[id_medicine_line[med_dict_key] - 1][2]['init_quantity'] += med_init_qty_line
                    #     mats[id_medicine_line[med_dict_key] - 1][2]['quantity'] += med_qty_line
                    #
                    # if mats[id_medicine_line[med_dict_key] - 1][2]['quantity'] > \
                    #         mats[id_medicine_line[med_dict_key] - 1][2]['init_quantity']:
                    #     over = True

                    if med_qty_line > med_init_qty_line:
                        over = True

        # chua co nguoi duyet phieu
        if not self.user_approval:
            self.write({'material_ids': mats, 'is_over_material': over})
        else:
            self.write({'material_ids': mats})

    def set_to_completed(self):
        if self.sudo().sale_order_id.check_order_missing_money():
            raise UserError(_(
                'Khách hàng chưa thanh toán đủ tiền theo SO nên không thể xác nhận hoàn thành phiếu khám!'))

        if self.sale_order_id.state == 'cancel':  # nếu SO đã bị hủy thì ko cho đóng phiếu khám
            raise ValidationError(_('Bạn không thể đóng phiếu khám khi SO gắn với phiếu khám đã bị hủy!'))

        # check số lượng dịch vụ kê ở phiếu khám đã được tạo phiếu chuyên khoa đủ
        service_surgery = self.surgeries_ids.mapped('services')
        service_specialty = self.specialty_ids.mapped('services')
        all_services = (service_surgery + service_specialty).ids

        walkin_services = self.service.ids

        missing_services = [s for s in walkin_services if s not in all_services]

        if missing_services:
            missing_services_record = self.env['sh.medical.health.center.service'].browse(missing_services).filtered(lambda s: s.is_no_specialty == False)
            #dịch vụ bắt buộc nhập phiếu chuyên khoa thì hiển thị thông báo
            if missing_services_record:
                missing_services_name = missing_services_record.mapped('name')
                raise UserError(_('Bạn chưa tạo phiếu chuyên khoa cho dịch vụ %s nên không thể xác nhận hoàn thành phiếu khám!' % missing_services_name ))

        # còn phiếu xn
        # if len(self.lab_test_ids.filtered(lambda lt: lt.state not in ["Completed"])) > 0:
        #     raise UserError(_('Bạn không thể đóng phiếu khi có phiếu xét nghiệm chưa được xác nhận hoàn thành!'))

        # còn phiếu cđha
        if len(self.imaging_ids.filtered(lambda lt: lt.state not in ["Completed"])) > 0:
            raise UserError(_(
                'Bạn không thể đóng phiếu khi có phiếu Chuẩn đoán hình ảnh - Thăm dò chức năng chưa được xác nhận hoàn thành!'))
        # còn phiếu pttt
        if len(self.surgeries_ids.filtered(lambda lt: lt.state not in ["Done", "Signed"])) > 0:
            raise UserError(
                _('Bạn không thể đóng phiếu khi có phiếu Phẫu thuật thủ thuật chưa được xác nhận hoàn thành!'))

        # còn phiếu chuyên khoa
        if len(self.specialty_ids.filtered(lambda lt: lt.state not in ["Done"])) > 0:
            raise UserError(_('Bạn không thể đóng phiếu khi có phiếu chuyên khoa chưa được xác nhận hoàn thành!'))

        # còn đơn thuốc
        if len(self.prescription_ids.filtered(lambda ints: ints.state in ["Draft","Sent to Pharmacy"])) > 0:
            raise UserError(_('Bạn không thể đóng phiếu khi có đơn thuốc chưa được xác nhận xuất!'))

        # còn phiếu nhập viên
        if len(self.inpatient_ids.filtered(lambda ints1: ints1.state not in ["Discharged", "Cancelled"])) > 0:
            raise UserError(_('Bạn không thể đóng phiếu lưu bệnh nhân chưa được xác nhận đã kết thúc chăm sóc!'))

        # còn phonecall
        service_has_phoncall = self.service.filtered(lambda s: s.is_no_phonecall == False)
        if service_has_phoncall:
            if not self.reexam_ids or len(self.reexam_ids.filtered(lambda lt: lt.state not in ["Confirmed"])) > 0:
                raise UserError(_('Bạn không thể đóng phiếu khi Hướng dẫn lịch tài khám chưa xác nhận hoàn thành!'))

        # cap nhat vat tu cho phieu kham
        # self.update_walkin_material()

        self.handle = self.handle if self.handle else 'discharge'
        self.date_out = self.date_out if self.date_out else datetime.datetime.now()
        self.close_walkin = date.today()

        # CẬP NHẬT SO LINK VỚI PHIẾU KHÁM TỪ NHÁP THÀNH Sale order
        if self.sale_order_id.state == 'draft':  # nếu SO vẫn ở trạng thái nháp thì chuyển thành SO
            self.sale_order_id.action_confirm()
            # sau khi xác nhận sẽ tự động tạo hóa đơn cho SO nếu chưa tạo
            # if self.sale_order_id.invoice_status == 'to invoice':
            #     # self.sale_order_id.action_confirm()
            #     wizard = self.env['sale.advance.payment.inv'].sudo().with_context(
            #         {'active_ids': [self.sale_order_id.id], 'patient': self.patient.id, 'company_id': self.sale_order_id.company_id.id}).create({})
            #     wizard.create_invoices()
        return self.write({'state': 'Completed'})  # cap nhat trang thai phieu kham

    def set_to_wait_payment(self):
        return self.write({'state': 'WaitPayment'})

    def set_to_progress(self):
        _logger.info(str(self.institution.name))

        if not self.institution:
            raise ValidationError(_('Không có cơ sở y tế gắn với công ty hiện tại!'))

        self = self.with_env(self.env(su=True))

        lab_test_wakin = []
        id_lab_test_wakin = self.lab_test_ids.mapped('test_type').ids

        img_test_wakin = []
        id_img_test_wakin = self.imaging_ids.mapped('test_type').ids

        surgery_wakin = []
        id_surgery_test_wakin = self.surgeries_ids.mapped('services').ids

        specialty_wakin = []
        id_specialty_test_wakin = self.specialty_ids.mapped('services').ids

        # TAO CÁC PHIEU XN, CĐHA, PTTT, CK NẾU CÓ
        seq_mat = 0
        for ser in self.service:
            if not self.lab_test_ids:
                # add lab test
                for lab in ser.lab_type_ids:
                    if lab.id not in id_lab_test_wakin:
                        lab_department = self.env['sh.medical.health.center.ward'].search(
                            [('institution', '=', self.institution.id), ('type', '=', 'Laboratory')], limit=1)

                        # ghi nhận case xn và vtth nếu có
                        lt_data = []
                        seq = 0
                        for lt in lab.material_ids:
                            seq += 1
                            lt_data.append((0, 0, {'sequence': seq,
                                                   'product_id': lt.product_id.id,
                                                   'init_quantity': lt.quantity,
                                                   'quantity': lt.quantity,
                                                   'is_init': True,
                                                   'uom_id': lt.uom_id.id}))
                        lt_case_data = []
                        seq_case = 0
                        for lt_case in lab.lab_criteria:
                            seq_case += 1
                            lt_case_data.append((0, 0, {'sequence': seq_case,
                                                        'name': lt_case.name,
                                                        'normal_range': lt_case.normal_range,
                                                        'units': lt_case.units.id,
                                                        'lab_test_criteria_id': lt_case.id,}))

                        id_lab_test_wakin.append(lab.id)  # co roi se khong add thêm nữa
                        pathologist = self.env['sh.medical.physician'].search([('speciality', '=', self.env.ref('shealth_all_in_one.23').id), ('institution', '=', self.institution.id), ('department', '=', lab_department.id)], limit=1)
                        lab_test_wakin.append((0, 0, {
                            'institution': self.institution.id,
                            'department': lab_department.id,
                            'test_type': lab.id,
                            'perform_room': self.env['sh.medical.health.center.ot'].search([('name', 'ilike', 'phòng xét nghiệm'), ('institution', '=', self.institution.id), ('department', '=', lab_department.id)], limit=1).id,
                            'has_child': lab.has_child,
                            'normal_range': lab.normal_range,
                            'patient': self.patient.id,
                            'pathologist': pathologist.id if pathologist else False,
                            'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                         "%Y-%m-%d %H:%M:%S") or fields.Datetime.now(),
                            # 'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                            #                                              "%Y-%m-%d %H:%M:%S") + timedelta(
                            #     minutes=15) or fields.Datetime.now(),
                            # 'date_analysis': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                            #                                             "%Y-%m-%d %H:%M:%S") + timedelta(
                            #     minutes=30) or fields.Datetime.now(),
                            # 'date_done': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                            #                                         "%Y-%m-%d %H:%M:%S") + timedelta(
                            #     hours=2) or fields.Datetime.now(),
                            'requestor': self.doctor.id,
                            'lab_test_material_ids': lt_data,
                            'lab_test_criteria': lt_case_data,
                            'walkin': self.id,
                            'state': 'Draft'}))

            if not self.imaging_ids:
                # add imaging test
                for img in ser.imaging_type_ids:
                    if img.id not in id_img_test_wakin:
                        img_department = self.env['sh.medical.health.center.ward'].search(
                            [('institution', '=', self.institution.id), ('type', '=', 'Laboratory')], limit=1)

                        # ghi nhận vtth nếu có
                        img_data = []
                        seq = 0
                        for ir in img.material_ids:
                            seq += 1
                            img_data.append((0, 0, {'sequence': seq,
                                                    'product_id': ir.product_id.id,
                                                    'init_quantity': ir.quantity,
                                                    'quantity': ir.quantity,
                                                    'is_init': True,
                                                    'uom_id': ir.uom_id.id}))

                        id_img_test_wakin.append(img.id)  # co roi se khong add thêm nữa
                        pathologist_img = self.env['sh.medical.physician'].search(
                            [('speciality', '=', self.env.ref('shealth_all_in_one.49').id),
                             ('institution', '=', self.institution.id), ('department', '=', img_department.id)],
                            limit=1)

                        # TỰ ĐỘNG HOÀN THÀNH PHIẾU CĐHA LUÔN
                        img_test_wakin.append((0, 0, {
                            'institution': self.institution.id,
                            'department': img_department.id,
                            'test_type': img.id,
                            'perform_room': self.env['sh.medical.health.center.ot'].search([('name', 'ilike', 'phòng siêu âm'), ('institution', '=', self.institution.id), ('department', '=', img_department.id)], limit=1).id,
                            'patient': self.patient.id,
                            'pathologist': pathologist_img.id if pathologist_img else False,
                            'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                         "%Y-%m-%d %H:%M:%S") + timedelta(
                                minutes=15) or fields.Datetime.now(),
                            'date_analysis': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                        "%Y-%m-%d %H:%M:%S") + timedelta(
                                minutes=30) or fields.Datetime.now(),
                            'date_done': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                    "%Y-%m-%d %H:%M:%S") + timedelta(
                                hours=2) or fields.Datetime.now(),
                            'requestor': self.doctor.id,
                            'imaging_material_ids': img_data,
                            'walkin': self.id,
                            'analysis': img.analysis,
                            'conclusion': img.conclusion,
                            'state': 'Completed'}))

        # neu là dich vu khoa phau thuat
        walkin_flag_surgery = False
        if self.service_room.related_department.type == 'Surgery':
            walkin_flag_surgery = True

        if len(self.service.filtered(lambda s: s.is_no_specialty == False)) > 0:
            if walkin_flag_surgery:
                if not self.surgeries_ids:
                    sur_department = self.env['sh.medical.health.center.ward'].search(
                        [('institution', '=', self.institution.id), ('type', '=', 'Surgery')], limit=1)

                    major_surgery_list = self.service.filtered(lambda s: s.surgery_type == 'major')

                    room_minor = False
                    room_major = False

                    sur_room = room_major if len(major_surgery_list) > 0 else room_minor
                    anesthetist_type = 'me' if len(major_surgery_list) > 0 else 'te'
                    surgery_wakin.append((0, 0, {
                        'institution': self.institution.id,
                        'department': sur_department.id,
                        'operating_room': sur_room,
                        'services': [(6, 0, self.service.filtered(lambda s: not s.is_no_specialty).ids)],
                        'pathology': self.pathology.id,
                        'anesthetist_type': anesthetist_type,
                        'surgical_diagram': ' '.join(map(str, self.service.mapped('surgical_diagram'))),
                        'surgical_order': ' '.join(map(str, self.service.mapped('surgical_order'))),
                        'patient': self.patient.id,
                        # 'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                        #                                              "%Y-%m-%d %H:%M:%S") + timedelta(
                        #     minutes=5) or self.date,
                        # 'surgery_date': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                        #                                            "%Y-%m-%d %H:%M:%S") + timedelta(
                        #     minutes=65) or self.date,
                        # 'surgery_end_date': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                        #                                                "%Y-%m-%d %H:%M:%S") + timedelta(
                        #     minutes=185) or self.date,
                        'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                     "%Y-%m-%d %H:%M:%S") + timedelta(
                            seconds=5) or self.date,
                        'surgery_date': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                   "%Y-%m-%d %H:%M:%S") + timedelta(
                            seconds=10) or self.date,
                        'surgery_end_date': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                       "%Y-%m-%d %H:%M:%S") + timedelta(
                            seconds=15) or self.date,
                        'surgeon': False,
                        'anesthetist': False,
                        'walkin': self.id,
                        'state': 'Draft'}))
            else:
                if not self.specialty_ids:
                    # _logger.info(self.service[0])
                    dep_detail = self.service[0].service_department.filtered(lambda s: s.institution == self.institution and s.type == self.related_department.type)
                    room_detail = self.service[0].service_room.filtered(lambda s: s.institution == self.institution and s.department == self.related_department)

                    if not dep_detail:
                        raise ValidationError(_('Bạn chưa cấu hình đủ khoa thực hiện cho dịch vụ!'))

                    if not room_detail:
                        raise ValidationError(_('Bạn chưa cấu hình đủ phòng thực hiện cho dịch vụ!'))

                    spec_department = dep_detail[0].id
                    spec_room = room_detail[0].id

                    physician_ck = False

                    specialty_wakin.append((0, 0, {
                        'institution': self.institution.id,
                        'department': spec_department,
                        'perform_room': spec_room,
                        'services': [(6, 0, self.service.filtered(lambda s: s.is_no_specialty == False).ids)],
                        'pathology': self.pathology.id,
                        'patient': self.patient.id,
                        # 'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                        #                                              "%Y-%m-%d %H:%M:%S") + timedelta(
                        #     minutes=5) or self.date,
                        # 'services_date': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                        #                                             "%Y-%m-%d %H:%M:%S") + timedelta(
                        #     minutes=35) or self.date,
                        # 'services_end_date': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                        #                                                 "%Y-%m-%d %H:%M:%S") + timedelta(
                        #     minutes=95) or self.date,
                        'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                     "%Y-%m-%d %H:%M:%S") + timedelta(
                            seconds=5) or self.date,
                        'services_date': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                    "%Y-%m-%d %H:%M:%S") + timedelta(
                            seconds=10) or self.date,
                        'services_end_date': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                        "%Y-%m-%d %H:%M:%S") + timedelta(
                            seconds=15) or self.date,
                        'physician': physician_ck,
                        'walkin': self.id,
                        'uom_price': self.uom_price,
                        'state': 'Draft'}))

        # vals = {'state': 'InProgress', 'surgeries_ids': surgery_wakin, 'imaging_ids': img_test_wakin, 'specialty_ids': specialty_wakin}

        vals = {'state': 'InProgress', 'lab_test_ids': lab_test_wakin, 'imaging_ids': img_test_wakin,
                'surgeries_ids': surgery_wakin, 'specialty_ids': specialty_wakin}
        empty_value = [key for key in vals if not vals[key]]
        for key in empty_value:
            vals.pop(key)
        return self.write(vals)

    def set_to_progress_admin(self):
        # mở lại trạng thái phiếu
        for record in self:
            record.sale_order_id.action_cancel()
            record.sale_order_id.action_draft()

        self.write({'state': 'InProgress'})

    def set_to_scheduled(self):
        # draft cac phieu lab, imaging, surgeries lien quan cua phieu kham
        # for lab in self.lab_test_ids:
        #     LabTest = self.env['sh.medical.lab.test'].browse(lab.id)
        #     if LabTest.state == 'Cancelled':
        #         LabTest.write({'state': 'Draft'})
        #
        # for imaging in self.imaging_ids:
        #     ImagingTest = self.env['sh.medical.imaging'].browse(imaging.id)
        #     if ImagingTest.state == 'Cancelled':
        #         ImagingTest.write({'state': 'Draft'})
        #
        # for surgery in self.surgeries_ids:
        #     Surgery = self.env['sh.medical.surgery'].browse(surgery.id)
        #     if Surgery.state == 'Cancelled':
        #         Surgery.write({'state': 'Draft'})

        return self.write({'state': 'Scheduled'})

    #HỦY PHIẾU KHÁM
    def set_to_cancelled(self):
        self.ensure_one()
        #hủy SO liên quan đến phiếu khám
        self.sale_order_id.action_cancel()
        # set các phiếu thu của phiếu khám bị hủy về False - Tương đương trạng thái đặt cọ
        self.payment_ids.write({'walkin': False})

        # xóa cac phieu lab, imaging lien quan cua phieu kham
        # for lab in self.lab_test_ids:
        #     LabTest = self.env['sh.medical.lab.test'].browse(lab.id)
        #     if LabTest.state == 'Draft':
        #         LabTest.unlink()
        #
        # for imaging in self.imaging_ids:
        #     ImagingTest = self.env['sh.medical.imaging'].browse(imaging.id)
        #     if ImagingTest.state == 'Draft':
        #         ImagingTest.unlink()

        # xóa cac phieu lien quan cua phieu kham
        for surgery in self.surgeries_ids:
            Surgery = self.env['sh.medical.surgery'].browse(surgery.id)
            if Surgery.state == 'Draft':
                Surgery.unlink()

        for specialty in self.specialty_ids:
            Specialty = self.env['sh.medical.specialty'].browse(specialty.id)
            if Specialty.state == 'Draft':
                Specialty.unlink()

        for inpatient in self.inpatient_ids:
            Inpatient = self.env['sh.medical.inpatient'].browse(inpatient.id)
            if Inpatient.state == 'Draft':
                Inpatient.unlink()

        for prescription in self.prescription_ids:
            Prescription = self.env['sh.medical.prescription'].browse(prescription.id)
            if Prescription.state == 'Draft':
                Prescription.unlink()

        for reexam in self.reexam_ids:
            Reexam = self.env['sh.medical.reexam'].browse(reexam.id)
            if Reexam.state == 'Draft':
                Reexam.unlink()

        # xử lý trạng thái của BK
        complete_walkin = self.env['sh.medical.appointment.register.walkin'].search(
            [('booking_id', '=', self.booking_id.id), ('id', '!=', self.id)])
        if not complete_walkin:
            self.booking_id.stage_id = self.env.ref('crm_base.crm_stage_confirm').id
        # đổi trạng thái phiếu khám thành đã hủy
        return self.write({'state': 'Cancelled'})

    # def set_to_cancelled(self):
    #     #cancel cac phieu lab, imaging, surgeries lien quan cua phieu kham
    #     for lab in self.lab_test_ids:
    #         LabTest = self.env['sh.medical.lab.test'].browse(lab.id)
    #         if LabTest.state == 'Draft':
    #             LabTest.write({'state': 'Cancelled'})
    #
    #     for imaging in self.imaging_ids:
    #         ImagingTest = self.env['sh.medical.imaging'].browse(imaging.id)
    #         if ImagingTest.state == 'Draft':
    #             ImagingTest.write({'state': 'Cancelled'})
    #
    #     for surgery in self.surgeries_ids:
    #         Surgery = self.env['sh.medical.surgery'].browse(surgery.id)
    #         if Surgery.state == 'Draft':
    #             Surgery.write({'state': 'Cancelled'})
    #
    #     return self.write({'state': 'Cancelled'})

    # Đưa phiếu khám về trạng thái KHÁM
    def return_draft_status(self):
        self.ensure_one()
        if self.state != 'WaitPayment':
            raise ValidationError('Chức năng này chỉ khả dụng khi phiếu ở trạng thái CHỜ THU TIỀN')
        else:
            self.set_to_scheduled()

    # Đưa phiếu khám về trạng thái KHÁM
    def return_draft_status_admin(self):
        self.ensure_one()
        if self.state == 'WaitPayment':
            self.set_to_scheduled()
        elif (self.state == 'Cancelled') and (self.sale_order_id.state == 'cancel'):
            self.set_to_scheduled()
            self.sale_order_id.state = 'draft'
        else:
            raise ValidationError('Chức năng này chỉ khả dụng khi phiếu ở trạng thái CHỜ THU TIỀN')

    # Tạo phiếu thu dạng nháp:
    def create_draft_payment(self):
        self.ensure_one()

        if self.service:
            # service_name = ''
            # total = self.sale_order_id.amount_total  # Số tiền lấy theo tổng số tiền trên SO đã link với phiếu
            # for ser in self.service:
            #     # total += ser.list_price
            #     service_name += ser.name + ";"
            #
            # journal_id = self.env['account.journal'].search(
            #     [('type', '=', 'cash'), ('company_id', '=', self.institution.his_company.id)], limit=1)
            # self.env['account.payment'].create({
            #     'partner_id': self.patient.partner_id.id,
            #     'patient': self.patient.id,
            #     'company_id': self.institution.his_company.id,
            #     'currency_id': self.institution.currency_id.id,
            #     'amount': total,
            #     'brand_id': self.institution.brand.id,
            #     'crm_id': self.booking_id.id,
            #     'communication': "Thu phí dịch vụ: " + service_name,
            #     'text_total': num2words_vnm(int(total)) + " đồng",
            #     'partner_type': 'customer',
            #     'payment_type': 'inbound',
            #     'payment_date': fields.Date.today(),  # ngày thanh toán
            #     'date_requested': fields.Date.today(),  # ngày yêu cầu
            #     'payment_method_id': self.env['account.payment.method'].search([('payment_type', '=', 'inbound')],
            #                                                                    limit=1).id,
            #     'journal_id': journal_id.id,
            #     'walkin': self.id,
            # })
            # return self.write({'state': 'WaitPayment'})

            # check số tiền đã thu và số tiền trong SO đã khớp chưa
            total_so = self.sudo().sale_order_id.amount_total  # Tổng tiền SO
            total_payment_walkin = self.sudo().sale_order_id.amount_remain  # Tổng tiền khách đã thanh toán
            total_so_owed = self.sudo().sale_order_id.amount_owed  # Tổng tiền khách nợ đã được duyệt

            draft_payment = False
            service_name = ''
            for ser in self.service:
                service_name += ser.name + ";"

            if self.payment_ids:
                draft_payment = self.sudo().payment_ids.search(
                    [('id', 'in', self.sudo().payment_ids.ids), ('state', '=', 'draft'),
                     ('payment_type', '=', 'inbound')], limit=1)
            if draft_payment:  # nếu có phiếu nháp thì chỉnh tiền và ghi chú ở phiếu nháp
                draft_payment = draft_payment.sudo()
                draft_payment.amount = total_so - total_payment_walkin - total_so_owed  # Số tiền cần thanh toán = tổng SO - tổng đã thanh toán - tổng nợ đã duyệt
                draft_payment.text_total = self.num2words_vnm(int(total_so - total_payment_walkin - total_so_owed)) + " đồng"
                draft_payment.communication = "Thu phí dịch vụ: " + service_name
                draft_payment.payment_date = fields.Date.today()
                draft_payment.date_requested = fields.Date.today()

            else:  # tạo mới nếu ko coa payment nháp
                journal_id = self.env['account.journal'].search(
                    [('type', '=', 'cash'), ('company_id', '=', self.env.company.id)], limit=1)
                self.env['account.payment'].create({
                    'name': False,
                    'partner_id': self.patient.partner_id.id,
                    'patient': self.patient.id,
                    'company_id': self.env.company.id,
                    'currency_id': self.env.company.currency_id.id,
                    'amount': total_so - total_payment_walkin - total_so_owed,
                    'brand_id': self.booking_id.brand_id.id,
                    'crm_id': self.booking_id.id,
                    'communication': "Thu phí dịch vụ: " + service_name,
                    'text_total': self.num2words_vnm(int(total_so - total_payment_walkin - total_so_owed)) + " đồng",
                    'partner_type': 'customer',
                    'payment_type': 'inbound',
                    'payment_date': datetime.date.today(),  # ngày thanh toán
                    'date_requested': datetime.date.today(),  # ngày yêu cầu
                    'payment_method_id': self.env['account.payment.method'].sudo().search(
                        [('payment_type', '=', 'inbound')], limit=1).id,
                    'journal_id': journal_id.id,
                    'walkin': self.id,
                })
            self.write({'state': 'WaitPayment'})  # chuyển trạng thái phiếu về chờ thanh toán

        else:
            raise ValidationError(_('You must select at least one service!'))

    def view_walkin(self):
        return {
            'name': _('Phiếu khám bệnh'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_view').id,
            'res_model': 'sh.medical.appointment.register.walkin',  # model want to display
            'target': 'current',  # if you want popup,
            # 'context': {'form_view_initial_mode': 'edit'},
            'res_id': self.id
        }

    def unlink(self):
        for walkin in self.filtered(lambda walkin: walkin.state not in ['Scheduled']):
            raise UserError(_('You can not delete a walkin record that is not in "Scheduled" stage !!'))
        return super(SHealthAppointmentWalkin, self).unlink()

    def reset_all_labtest(self):
        for labtest in self.lab_test_ids.filtered(lambda lab: lab.state == 'Draft'):
            labtest.unlink()

    def add_config_labtest(self):
        lab_test_wakin = []
        id_lab_test_wakin = self.lab_test_ids.mapped('test_type').ids

        # TAO CÁC PHIEU XN - NẾU CÓ
        for ser in self.service:
            if not self.lab_test_ids:
                # add lab test
                for lab in ser.lab_type_ids:
                    if lab.id not in id_lab_test_wakin:
                        lab_department = self.env['sh.medical.health.center.ward'].search(
                            [('institution', '=', self.institution.id), ('type', '=', 'Laboratory')], limit=1)

                        # ghi nhận case xn và vtth nếu có
                        lt_data = []
                        seq = 0
                        for lt in lab.material_ids:
                            seq += 1
                            lt_data.append((0, 0, {'sequence': seq,
                                                   'product_id': lt.product_id.id,
                                                   'init_quantity': lt.quantity,
                                                   'quantity': lt.quantity,
                                                   'is_init': True,
                                                   'uom_id': lt.uom_id.id}))
                        lt_case_data = []
                        seq_case = 0
                        for lt_case in lab.lab_criteria:
                            seq_case += 1
                            lt_case_data.append((0, 0, {'sequence': seq_case,
                                                        'name': lt_case.name,
                                                        'normal_range': lt_case.normal_range,
                                                        'units': lt_case.units.id,
                                                        'lab_test_criteria_id': lt_case.id,}))

                        id_lab_test_wakin.append(lab.id)  # co roi se khong add thêm nữa
                        # print(lt_case_data)
                        pathologist = self.env['sh.medical.physician'].search([('speciality', '=', self.env.ref('shealth_all_in_one.23').id), ('institution', '=', self.institution.id), ('department', '=', lab_department.id)], limit=1)
                        lab_test_wakin.append((0, 0, {
                            'institution': self.institution.id,
                            'department': lab_department.id,
                            'test_type': lab.id,
                            'perform_room': self.env['sh.medical.health.center.ot'].search([('name', 'ilike', 'phòng xét nghiệm'), ('institution', '=', self.institution.id), ('department', '=', lab_department.id)], limit=1).id,
                            'has_child': lab.has_child,
                            'normal_range': lab.normal_range,
                            'patient': self.patient.id,
                            'pathologist': pathologist.id if pathologist else False,
                            'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                         "%Y-%m-%d %H:%M:%S") + timedelta(
                                minutes=15) or fields.Datetime.now(),
                            'date_analysis': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                        "%Y-%m-%d %H:%M:%S") + timedelta(
                                minutes=30) or fields.Datetime.now(),
                            # 'date_done': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                            #                                         "%Y-%m-%d %H:%M:%S") + timedelta(
                            #     hours=2) or fields.Datetime.now(),
                            'requestor': self.doctor.id,
                            'lab_test_material_ids': lt_data,
                            'lab_test_criteria': lt_case_data,
                            'walkin': self.id,
                            'state': 'Draft'}))
                        # print(lt_case_data)
        vals = {'lab_test_ids': lab_test_wakin}
        empty_value = [key for key in vals if not vals[key]]
        for key in empty_value:
            vals.pop(key)
        return self.write(vals)

    # This function prints the assign lab test

    def print_assign_patient_labtest(self):
        return self.env.ref('shealth_all_in_one.action_report_assign_patient_labtest').report_action(self)

    # This function prints the result lab test

    def print_result_patient_labtest(self):
        return self.env.ref('shealth_all_in_one.action_report_result_patient_labtest').report_action(self)

    # This function prints the assign img test

    def print_assign_patient_imaging(self):
        for img in self.imaging_ids:
            if not img.perform_room:
                raise Warning(
                    _('Bạn chưa chỉ định hết phòng thực hiện cho các phiếu CĐHA - TDCN.'))

        return self.env.ref('shealth_all_in_one.action_report_assign_patient_imaging_multi').report_action(self)

    # This function prints the result img test
    def print_result_patient_imaging(self):
        return self.env.ref('shealth_all_in_one.action_result_result_patient_imaging').report_action(self)

    # This function prints the assign services
    def print_assign_patient_services(self):
        return self.env.ref('shealth_all_in_one.action_report_assign_patient_services').report_action(self)

    # This function prints the advisory services
    def print_assign_patient_services_advisory(self):
        return self.env.ref('shealth_all_in_one.action_report_assign_patient_services_advisory').report_action(self)

    def get_detail_walkin_services(self,product_id):
        for record in self:
            service_detail = self.env['sh.medical.health.center.service'].sudo().search(
                [('product_id', '=', product_id.id)], limit=1)

            his_service_type_text = str(dict(service_detail._fields['his_service_type']._description_selection(self.env)).get(service_detail.his_service_type))

            list_done_walkin = record.booking_id.walkin_ids.filtered(lambda w: service_detail.id in w.service.ids and w.state == 'Completed').sorted('service_date').mapped('service_date')
            index = [i for i, x in enumerate(list_done_walkin) if x == record.service_date]
            if len(list_done_walkin) > 0 and len(index) > 0:
                num = index[0] + 1
                print("Đã có phiếu khám hoàn thành")
            else:
                print("Chưa có phiếu khám hoàn thành")
                num = len(list_done_walkin) + 1
            return [his_service_type_text,num]

    def get_detail_walkin_labs(self):
        for record in self:
            ret_val = []
            group_list_labs = self.env['sh.medical.lab.test'].read_group([('id', 'in', record.lab_test_ids.ids)], ['id'], ['date_requested:day'], orderby='date_requested desc')

            for group_lab in group_list_labs:
                lab = self.env['sh.medical.lab.test'].search(group_lab['__domain']).mapped('id')
                ret_val.append(self.env['sh.medical.lab.test'].browse(lab))
            return ret_val

# Physician schedule management for Walkins
class SHealthPhysicianWalkinSchedule(models.Model):
    _name = "sh.medical.physician.walkin.schedule"
    _description = "Information about walkin schedule"

    name = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    physician_id = fields.Many2one('sh.medical.physician', string='Physician', index=True, ondelete='cascade')

    _order = 'name desc'

# TODO Chuyen sang model chinh
# Inheriting Physician screen to add walkin schedule lines
class SHealthPhysician(models.Model):
    _inherit = "sh.medical.physician"
    # walkin_schedule_lines = fields.One2many('sh.medical.physician.walkin.schedule', 'physician_id', string='Walkin Schedule')
    walkin = fields.One2many('sh.medical.appointment.register.walkin', 'doctor', string='Walkin Schedule')


# Inheriting Inpatient module to add "Walkin" screen reference
class shealthInpatient(models.Model):
    _inherit = 'sh.medical.inpatient'
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', ondelete='cascade')
    services_domain = fields.Many2many('sh.medical.health.center.service', related='walkin.service',
                                       string="Services Domain")
    allow_institutions = fields.Many2many('sh.medical.health.center', string='Allow institutions', related='walkin.allow_institutions')

    @api.onchange('walkin')
    def _onchange_walkin(self):
        if self.walkin:
            self.patient = self.walkin.patient
            self.admission_reason = self.walkin.pathology
            self.admission_reason_walkin = self.walkin.reason_check
            self.services = [(6, 0, self.walkin.service.filtered(lambda s: not s.is_no_specialty).ids)]


class shealthWalkinReexam(models.Model):
    _inherit = 'sh.medical.reexam'

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', ondelete='cascade')
    service_related = fields.Many2many('sh.medical.health.center.service', string='Services related',
                                       related='walkin.service')

    @api.onchange('walkin')
    def domain_company(self):
        self.company = self.walkin.company_id.id
        if self.walkin and self.walkin.company2_id:
            # self.company = self.walkin.company2_id[0]._origin.id
            return {'domain': {'company': [('id', 'in', [self.walkin.company_id.id, self.walkin.company2_id._origin.ids])]}}
        else:
            # self.company = self.walkin.company_id.id
            return {'domain': {'company': [('id', 'in', [self.walkin.company_id.id])]}}

    @api.onchange('walkin')
    def _onchange_walkin(self):
        if self.walkin:
            self.patient = self.walkin.patient
            self.services = [(6, 0, self.walkin.service.filtered(lambda s: not s.is_no_specialty).ids)]

# Inheriting vaccines module to add "Walkin" screen reference
class SHealthVaccines(models.Model):
    _inherit = 'sh.medical.vaccines'
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', ondelete='cascade')


# Inheriting Patient module to add "Walkin" screen reference
class SHealthPatient(models.Model):
    _inherit = 'sh.medical.patient'

    def _walkin_count(self):
        sh_walkin = self.env['sh.medical.appointment.register.walkin']
        for pa in self:
            domain = [('patient', '=', pa.id)]
            walk_ids = sh_walkin.search(domain)
            walk = sh_walkin.browse(walk_ids)
            walk_count = 0
            for wk in walk:
                walk_count += 1
            pa.walkin_count = walk_count
        return True

    walkin = fields.One2many('sh.medical.appointment.register.walkin', 'patient', string='Registers of walkin')
    walkin_count = fields.Integer(compute=_walkin_count, string="Register of walkin")


