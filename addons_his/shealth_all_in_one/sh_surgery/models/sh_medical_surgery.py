# -*- encoding: utf-8 -*-
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

import time

import base64
import calendar
import datetime
import logging
from datetime import timedelta
from io import BytesIO
from odoo import fields, api, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools import pycompat
from .mailmerge import MailMerge

_logger = logging.getLogger(__name__)


class SHealthSurgeryRCRI(models.Model):
    _name = "sh.medical.surgery.rcri"
    _description = "Revised Cardiac Risk Index"

    RCRI_CLASS = [
        ('I', 'I'),
        ('II', 'II'),
        ('III', 'III'),
        ('IV', 'IV'),
    ]

    def get_rcri_name(self):
        result = {}
        rcri_name = ''
        for rc in self:
            rcri_name = 'Points: ' + str(rc.rcri_total) + ' (Class ' + str(rc.rcri_class) + ')'
            rc.name = rcri_name
        return result

    name = fields.Char(compute=get_rcri_name, string="RCRI", size=64)
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True)
    doctor = fields.Many2one('sh.medical.physician', string='Physician', domain=[('is_pharmacist', '=', False)],
                             help="Health professional / Cardiologist who signed the assesment RCRI")
    rcri_date = fields.Datetime('Date', required=True, default=lambda *a: datetime.datetime.now())
    rcri_high_risk_surgery = fields.Boolean(string='High Risk surgery',
                                            help='Includes andy suprainguinal vascular, intraperitoneal or intrathoracic procedures')
    rcri_ischemic_history = fields.Boolean(string='History of Ischemic heart disease',
                                           help='History of MI or a positive exercise test, current complaint of chest pain considered to be secondary to myocardial ischemia, use of nitrate therapy, or ECG with pathological Q waves; do not count prior coronary revascularization procedure unless one of the other criteria for ischemic heart disease is present"')
    rcri_congestive_history = fields.Boolean(string='History of Congestive heart disease')
    rcri_diabetes_history = fields.Boolean(string='Preoperative Diabetes',
                                           help="Diabetes Mellitus requiring treatment with Insulin")
    rcri_cerebrovascular_history = fields.Boolean(string='History of Cerebrovascular disease')
    rcri_kidney_history = fields.Boolean(string='Preoperative Kidney disease',
                                         help="Preoperative serum creatinine >2.0 mg/dL (177 mol/L)")
    rcri_total = fields.Integer(string='Score', help='Points 0: Class I Very Low (0.4% complications)\n'
                                                     'Points 1: Class II Low (0.9% complications)\n'
                                                     'Points 2: Class III Moderate (6.6% complications)\n'
                                                     'Points 3 or more : Class IV High (>11% complications)',
                                default=lambda *a: 0)
    rcri_class = fields.Selection(RCRI_CLASS, string='RCRI Class', required=True, default=lambda *a: 'I')

    @api.onchange('rcri_high_risk_surgery', 'rcri_ischemic_history', 'rcri_congestive_history', 'rcri_diabetes_history',
                  'rcri_cerebrovascular_history', 'rcri_kidney_history')
    def on_change_with_rcri(self):
        total = 0
        rcri_class = 'I'
        if self.rcri_high_risk_surgery:
            total = total + 1
        if self.rcri_ischemic_history:
            total = total + 1
        if self.rcri_congestive_history:
            total = total + 1
        if self.rcri_diabetes_history:
            total = total + 1
        if self.rcri_kidney_history:
            total = total + 1
        if self.rcri_cerebrovascular_history:
            total = total + 1

        self.rcri_total = total

        if total == 1:
            rcri_class = 'II'
        if total == 2:
            rcri_class = 'III'
        if (total > 2):
            rcri_class = 'IV'

        self.rcri_class = rcri_class


class SHealthSurgeryTeam(models.Model):
    _name = "sh.medical.surgery.team"
    _description = "Surgery Team"

    # def get_domain_surgeon(self):
    #     if self.env.ref('shealth_all_in_one.45', False):
    #         return [('is_pharmacist', '=', False), ('speciality', '=', self.env.ref('shealth_all_in_one.45').id)]
    #     else:
    #         return [('is_pharmacist', '=', False)]
    #
    # def get_domain_nurse(self):
    #     if self.env.ref('shealth_all_in_one.33', False):
    #         return [('is_pharmacist', '=', False), ('speciality', '=', self.env.ref('shealth_all_in_one.33').id)]
    #     else:
    #         return [('is_pharmacist', '=', False)]

    # _sql_constraints = [('name_unique', 'unique(name,team_member,service_performances,role)',
    #                      "Vai trò của thành viên với dịch vụ phải là duy nhất!")]

    @api.constrains('name', 'team_member', 'service_performances', 'role')
    def _check_constrains_team_member(self):
        for rec in self:
            similars = self.env['sh.medical.surgery.team'].search(
                [('id', '!=', rec.id), ('name', '=', rec.name.id), ('team_member', '=', rec.team_member.id),
                 ('role', '=', rec.role.id)])
            if similars:
                for sim_rec in similars:
                    for rec_service in rec.service_performances:
                        if rec_service in sim_rec.service_performances:
                            raise ValidationError('Vai trò của thành viên với dịch vụ phải là duy nhất!')

    def get_domain_role(self):
        if self.env.context.get('department_type'):
            return [('type', '=', self.env.context.get('department_type').lower())]
        else:
            return [('type', '=', 'surgery')]

    name = fields.Many2one('sh.medical.surgery', string='Surgery')
    team_member = fields.Many2one('sh.medical.physician', string='Thành viên',
                                  help="Health professional that participated on this surgery",
                                  domain=[('is_pharmacist', '=', False)], required=True)
    # doctor_member = fields.Many2many('sh.medical.physician', 'sh_surgery_doctor_rel', 'surgery_id', 'doctor_id',
    #                  string='Doctor', required=True, domain=lambda self:self.get_domain_surgeon()
    #                  #domain=lambda self: [('speciality', '=', self.env.ref('shealth_all_in_one.45').id)]
    # )
    # nursing_member = fields.Many2many('sh.medical.physician', 'sh_surgery_nursing_rel', 'surgery_id', 'nursing_id',
    #                                  string='Nursing',required=True, domain=lambda self:self.get_domain_nurse()
    #                  #domain = lambda self: [('speciality', '=', self.env.ref('shealth_all_in_one.33').id)]
    # )
    service_performance = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ thực hiện',
                                          help="Service that persons participated on this surgery")

    service_performances = fields.Many2many('sh.medical.health.center.service', 'sh_surgery_team_services_rel',
                                            'surgery_team_id', 'service_id',
                                            string='Những dịch vụ thực hiện',
                                            help="Các dịch vụ của thành viên với vai trò này thực hiện")

    role = fields.Many2one('sh.medical.team.role', string='Vai trò', domain=lambda self: self.get_domain_role())
    notes = fields.Char(string='Notes')

    # @api.onchange('team_member')
    # def onchange_team_member(self):
    #     if self.team_member:
    #         if self.team_member.speciality:
    #             self.role = self.team_member.speciality.id


class SHealthSurgerySupply(models.Model):
    _name = "sh.medical.surgery.supply"
    _description = "Supplies related to the surgery"

    MEDICAMENT_TYPE = [
        ('Medicine', 'Medicine'),
        ('Supplies', 'Supplies'),
        ('CCDC', 'CCDC')
    ]
    EXPLANATION_SUPPLY = [
        ('doctor_appointed', 'Theo y lệnh bác sĩ'),
        ('not_in_the_bom', 'Không có trong BOM'),
        ('other', 'Khác'),
    ]

    name = fields.Many2one('sh.medical.surgery', string='Surgery')
    qty = fields.Float(string='Initial required quantity', digits='Product Unit of Measure', required=True,
                       help="Initial required quantity", default=lambda *a: 0)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    supply = fields.Many2one('sh.medical.medicines', string='Supply', required=True,
                             help="Supply to be used in this surgery", domain=lambda self: [
            ('categ_id', 'child_of', self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    notes = fields.Char(string='Notes')
    explanation_supply = fields.Selection(EXPLANATION_SUPPLY, string='Giải trình')
    is_diff_bom = fields.Boolean('Khác định mức?', compute='compute_qty_used_bom')
    qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
                             compute='compute_available_qty_supply')
    qty_in_loc = fields.Float(string='Số lượng tại tủ', required=True, help="Số lượng khả dụng trong tủ trực",
                              compute='compute_available_qty_supply_in_location')
    is_warning_location = fields.Boolean('Cảnh báo tại tủ', compute='compute_available_qty_supply_in_location')
    qty_used = fields.Float(string='Actual quantity used', digits=dp.get_precision('Product Unit of Measure'),
                            required=True, help="Actual quantity used", default=lambda *a: 1)
    location_id = fields.Many2one('stock.location', 'Stock location', domain="[('usage', '=', 'internal')]")
    medicament_type = fields.Selection(MEDICAMENT_TYPE, related="supply.medicament_type", string='Medicament Type',
                                       store=True)

    services = fields.Many2many('sh.medical.health.center.service', 'sh_surgery_supply_service_rel',
                                track_visibility='onchange',
                                string='Dịch vụ thực hiện')
    service_related = fields.Many2many('sh.medical.health.center.service', 'sh_surgery_supply_service_related_rel',
                                       related="name.services",
                                       string='Dịch vụ liên quan')

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự

    picking_id = fields.Many2one('stock.picking', string='Phiếu điều chuyển')

    @api.depends('qty_used', 'qty')
    def compute_qty_used_bom(self):
        for record in self:
            if record.qty_used > record.qty:
                record.is_diff_bom = True
            else:
                record.is_diff_bom = False

    @api.depends('supply', 'uom_id')
    def compute_available_qty_supply(self):  # so luong kha dung toan vien
        for record in self:
            if record.supply:
                record.qty_avail = record.uom_id._compute_quantity(record.supply.qty_available,
                                                                   record.supply.uom_id) if record.uom_id != record.supply.uom_id else record.supply.qty_available
            else:
                record.qty_avail = 0

    @api.depends('supply', 'location_id', 'qty_used', 'uom_id')
    def compute_available_qty_supply_in_location(self):  # so luong kha dung tai tu
        for record in self:
            if record.supply:
                quantity_on_hand = self.env['stock.quant'].with_user(1)._get_available_quantity(
                    record.supply.product_id,
                    record.location_id)  # check quantity trong location

                record.qty_in_loc = record.uom_id._compute_quantity(quantity_on_hand,
                                                                    record.supply.uom_id) if record.uom_id != record.supply.uom_id else quantity_on_hand
            else:
                record.qty_in_loc = 0

            record.is_warning_location = True if (
                    record.qty_used > record.qty_in_loc or record.qty_in_loc == 0) else False

    @api.onchange('qty_used', 'supply')
    def onchange_qty_used(self):
        if self.qty_used < 0 and self.supply:
            raise UserError(_("Số lượng nhập phải lớn hơn 0!"))

    @api.onchange('supply')
    def _change_product_id(self):
        self.uom_id = self.supply.uom_id
        # mặc định dịch vụ theo phiếu
        self.services = self.name.services
        domain = {'domain': {'uom_id': [('category_id', '=', self.supply.uom_id.category_id.id)]}}
        if self.medicament_type == 'Medicine':
            self.location_id = self.name.operating_room.location_medicine_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'medicine'),
                                               ('company_id', '=', self.name.institution.his_company.id)]
        elif self.medicament_type == 'Supplies':
            self.location_id = self.name.operating_room.location_supply_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'supply'),
                                               ('company_id', '=', self.name.institution.his_company.id)]

        return domain

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.supply.uom_id.category_id:
            self.uom_id = self.supply.uom_id
            raise Warning(
                _('The Supply Unit of Measure and the Material Unit of Measure must be in the same category.'))


# class SHealthSurgeryMedicine(models.Model):
#     _name = "sh.medical.surgery.medicines"
#     _description = "Medicines related to the surgery"
#
#     name = fields.Many2one('sh.medical.surgery', string='Surgery')
#     qty = fields.Integer(string='Initial required quantity',digits='Product Unit of Measure', required=True, help="Initial required quantity", default=lambda *a: 0)
#     uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
#     medicine = fields.Many2one('product.product', string='Supply', required=True, help="Medicines to be used in this surgery", domain=lambda self:[('categ_id','=',self.env.ref('shealth_all_in_one.sh_medicines').id)])
#     # medicines = fields.Many2one('product.product', string='Supply', required=True, help="Supply to be used in this surgery", domain=lambda self:[('categ_id','child_of',self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
#     notes = fields.Char(string='Notes')
#     qty_used = fields.Float(string='Actual quantity used', required=True, help="Actual quantity used", default=lambda *a: 0)
#
#     @api.onchange('medicines')
#     def _change_product_id(self):
#         self.uom_id = self.medicines.uom_id
#
#     @api.onchange('uom_id')
#     def _change_uom_id(self):
#         if self.uom_id.category_id != self.medicine.uom_id.category_id:
#             self.uom_id = self.supply.uom_id
#             raise Warning(
#                 _('The Medicines Unit of Measure and the Material Unit of Measure must be in the same category.'))


class SHealthSurgery(models.Model):
    _name = "sh.medical.surgery"
    _description = "Surgerical Management"

    _order = "walkin"

    _inherit = ['mail.thread']

    # CLASSIFICATION = [
    #     ('Optional', 'Optional'),
    #     ('Required', 'Required'),
    #     ('Urgent', 'Urgent'),
    #     ('Emergency', 'Emergency'),
    # ]

    STATES = [
        ('Draft', 'Draft'),
        ('Confirmed', 'Confirmed'),
        ('In Progress', 'In Progress'),
        ('Done', 'Done'),
        ('Signed', 'Signed'),
        ('Cancelled', 'Cancelled'),
    ]

    GENDER = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Female -> Male', 'Female -> Male'),
        ('Male -> Female', 'Male -> Female'),
    ]

    # PREOP_MALLAMPATI = [
    #     ('Class 1', 'Class 1: Full visibility of tonsils, uvula and soft '
    #                 'palate'),
    #     ('Class 2', 'Class 2: Visibility of hard and soft palate, '
    #                 'upper portion of tonsils and uvula'),
    #     ('Class 3', 'Class 3: Soft and hard palate and base of the uvula are '
    #                 'visible'),
    #     ('Class 4', 'Class 4: Only Hard Palate visible'),
    # ]

    # PREOP_ASA = [
    #     ('PS 1', 'PS 1 : Normal healthy patient'),
    #     ('PS 2', 'PS 2 : Patients with mild systemic disease'),
    #     ('PS 3', 'PS 3 : Patients with severe systemic disease'),
    #     ('PS 4', 'PS 4 : Patients with severe systemic disease that is'
    #              ' a constant threat to life '),
    #     ('PS 5', 'PS 5 : Moribund patients who are not expected to'
    #              ' survive without the operation'),
    #     ('PS 6', 'PS 6 : A declared brain-dead patient who organs are'
    #              ' being removed for donor purposes'),
    # ]

    # SURGICAL_WOUND = [
    #     ('I', 'Clean . Class I'),
    #     ('II', 'Clean-Contaminated . Class II'),
    #     ('III', 'Contaminated . Class III'),
    #     ('IV', 'Dirty-Infected . Class IV'),
    # ]

    REGION = [
        ('North', 'Miền Bắc'),
        ('South', 'Miền Nam')
    ]
    # Nếu ai thêm pp vô cảm thì hãy thêm cả ở PP_VO_CAM_DICT để k gặp lỗi
    PP_VO_CAM = [
        ('te_tai_cho', 'Tê tại chỗ'),
        ('te_me_co_thu_phi', 'Tiền mê có thu phí'),
        ('te_me_theo_chi_dinh_bac_sy', 'Tiền mê theo chỉ định bác sỹ'),
        ('me_tinh_mach', 'Mê tĩnh mạch'),
        ('gay_te_tuy_song', 'Gây tê tủy sống'),
        ('gay_me_mask_thanh_quan', 'Gây mê mask thanh quản'),
        ('gay_me_nkq_duoi_4_h', 'Gây mê NKQ < 4 giờ'),
        ('gay_me_nkq_tren_4_h', 'Gây mê NKQ > 4 giờ'),
        ('te_tai_cho_mask_tq', 'Tê tại chỗ + Mask TQ'),
        ('te_tai_cho_me_nkq_duoi_4h', 'Tê tại chỗ + Mê NKQ < 4 h'),
        ('te_tai_cho_me_nkq_tren_4h', 'Tê tại chỗ + Mê NKQ > 4 h'),
        ('tien_me_te_tai_cho_mask_tq', 'Tiền mê + Tê tại chỗ + mask TQ'),
        ('tien_me_te_tai_cho_me_nkq_duoi_4h', 'Tiền mê + Tê tại chỗ + Mê NKQ < 4h'),
        ('tien_me_te_tai_cho_me_nkq_tren_4h', 'Tiền mê + Tê tại chỗ + Mê NKQ > 4h'),
        ('te', 'Gây tê'),
        ('tien_me', 'Tiền mê'),
        ('me', 'Gây mê'),
    ]



    def _surgery_duration(self):
        for su in self:
            su.surgery_length = False
            if su.surgery_end_date and su.surgery_date:
                surgery_date = 1.0 * calendar.timegm(
                    time.strptime(su.surgery_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))
                surgery_end_date = 1.0 * calendar.timegm(
                    time.strptime(su.surgery_end_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))
                duration = (surgery_end_date - surgery_date) / 3600
                su.surgery_length = duration
        return True

    def _patient_age_at_surgery(self):
        def compute_age_from_dates(patient_dob, patient_surgery_date):
            if patient_dob and patient_surgery_date:
                dob = datetime.datetime.strptime(patient_dob.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
                surgery_date = datetime.datetime.strptime(patient_surgery_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                          '%Y-%m-%d %H:%M:%S').date()
                delta = surgery_date - dob
                # years_months_days = _(str(delta.days // 365)+" years "+ str(delta.days%365)+" days")
                # years_months_days = _("%s tuổi %s ngày"%(str(delta.days // 365),str(delta.days%365)))
                years_months_days = _("%s tuổi" % (str(delta.days // 365)))
            else:
                years_months_days = _("No DoB !")
            return years_months_days

        result = {}
        for patient_data in self:
            patient_data.computed_age = compute_age_from_dates(patient_data.patient.birth_date,
                                                               patient_data.surgery_date)
        return result

    def _get_surgeon(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    def get_domain_surgeon(self):
        # Phẫu thuật thẩm mỹ id=45 => 6
        return [('is_pharmacist', '=', False), ('speciality', '=', 6)]
        # if self.env.ref('shealth_all_in_one.45', False):
        #     return [('is_pharmacist', '=', False), ('speciality', '=', self.env.ref('shealth_all_in_one.45').id)]
        # else:
        #     return [('is_pharmacist', '=', False)]

    def get_domain_anesthetist(self):
        # Gây me id=5 => 1
        return [('is_pharmacist', '=', False), ('speciality', '=', 1)]
        # if self.env.ref('shealth_all_in_one.5', False):
        #     return [('is_pharmacist', '=', False), ('speciality', '=', self.env.ref('shealth_all_in_one.5').id)]
        # else:
        #     return [('is_pharmacist', '=', False)]

    name = fields.Char(string='Surgery #', size=64, readonly=True, required=True, default=lambda *a: '/')
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True,
                              states={'Draft': [('readonly', False)]})
    # admission = fields.Many2one('sh.medical.appointment', string='Admission',
    #                             help="Patient Name", readonly=True,
    #                             states={'Draft': [('readonly', False)]})
    # procedures = fields.Many2many('sh.medical.procedure', 'sh_surgery_procedure_rel', 'surgery_id', 'procedure_id', string='Procedures', help="List of the procedures in the surgery. Please enter the first one as the main procedure", readonly=True,states={'In Progress': [('readonly', False)]})
    pathology = fields.Many2one('sh.medical.pathology', string='Condition', help="Base Condition / Reason",
                                readonly=True, states={'Draft': [('readonly', False)]})
    services = fields.Many2many('sh.medical.health.center.service', 'sh_surgery_service_rel', 'surgery_id',
                                'service_id',
                                domain="[('service_department', '=', department)]", readonly=False,
                                states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
                                track_visibility='onchange', string='Services')
    # classification = fields.Selection(CLASSIFICATION, string='Urgency', help="Urgency level for this surgery",
    #                                   readonly=True, states={'Draft': [('readonly', False)]})
    surgeon = fields.Many2one('sh.medical.physician', string='Surgeon', help="Surgeon who did the procedure",
                              domain=lambda self: self.get_domain_surgeon(),
                              readonly=False, states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
                              default=_get_surgeon)
    anesthetist = fields.Many2one('sh.medical.physician', string='Anesthetist', help="Anesthetist in charge",
                                  domain=lambda self: self.get_domain_anesthetist(),
                                  readonly=False, states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    date_requested = fields.Datetime(string='Ngày giờ chỉ định',
                                     help="Ngày giờ chỉ định",
                                     readonly=False,
                                     states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
                                     default=fields.Datetime.now)
    surgery_date = fields.Datetime(string='Start date & time', help="Start of the Surgery",
                                   default=fields.Datetime.now)
    surgery_end_date = fields.Datetime(string='End date & time', help="End of the Surgery")
    surgery_length = fields.Float(compute=_surgery_duration, string='Duration (Hour:Minute)',
                                  help="Length of the surgery", readonly=False,
                                  states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    computed_age = fields.Char(compute=_patient_age_at_surgery, size=32, string='Age during surgery',
                               help="Computed patient age at the moment of the surgery", readonly=False,
                               states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    # gender = fields.Selection(GENDER, string='Gender', readonly=True, states={'Draft': [('readonly', False)]})
    # signed_by = fields.Many2one('res.users', string='Signed by',
    #                             help="Health Professional that signed this surgery document")
    description = fields.Text(string='Description', readonly=True,
                              states={'Draft': [('readonly', False)], 'Confirmed': [('readonly', False)],
                                      'In Progress': [('readonly', False)]})

    # preop_mallampati = fields.Selection(PREOP_MALLAMPATI, string='Mallampati Score', readonly=True,
    #                                     states={'Draft': [('readonly', False)]})
    preop_bleeding_risk = fields.Boolean(string='Risk of Massive bleeding',
                                         help="Patient has a risk of losing more than 500 ml in adults of over 7ml/kg in infants. If so, make sure that intravenous access and fluids are available",
                                         readonly=True, states={'Draft': [('readonly', False)]})
    preop_oximeter = fields.Boolean(string='Pulse Oximeter in place', help="Pulse oximeter is in place and functioning",
                                    readonly=True, states={'Draft': [('readonly', False)]})
    preop_site_marking = fields.Boolean(string='Surgical Site Marking',
                                        help="The surgeon has marked the surgical incision",
                                        readonly=True,
                                        states={'Draft': [('readonly', False)]})
    preop_antibiotics = fields.Boolean(string='Antibiotic Prophylaxis',
                                       help="Prophylactic antibiotic treatment within the last 60 minutes",
                                       readonly=True, states={'Draft': [('readonly', False)]})
    preop_sterility = fields.Boolean(string='Sterility Confirmed',
                                     help="Nursing team has confirmed sterility of the devices and room", readonly=True,
                                     states={'Draft': [('readonly', False)]})
    # preop_asa = fields.Selection(PREOP_ASA, string='ASA PS',
    #                              help="ASA pre-operative Physical Status",
    #                              readonly=True,
    #                              states={'Draft': [('readonly', False)]})
    # preop_rcri = fields.Many2one('sh.medical.surgery.rcri', string='RCRI',
    #                              help='Patient Revised Cardiac Risk Index\n Points 0: Class I Very Low (0.4% complications)\n Points 1: Class II Low (0.9% complications)\n Points 2: Class III Moderate (6.6% complications)\n Points 3 or more : Class IV High (>11% complications)',
    #                              readonly=True, states={'Draft': [('readonly', False)]})
    preop_vital_signs = fields.Boolean(string='Đo dấu hiệu sinh tồn',
                                       help="Xác nhận đã đo dấu hiệu sinh tồn trước mổ", readonly=True,
                                       states={'Draft': [('readonly', False)]})
    preop_normal_check = fields.Boolean(string='Khám sức khỏe trước phẫu thuật',
                                        help="Xác nhận đã Khám sức khỏe trước phẫu thuật", readonly=True,
                                        states={'Draft': [('readonly', False)]})
    preop_signed_commitment = fields.Boolean(string='Ký hồ sơ, cam kết',
                                             help="Xác nhận khách đã Ký hồ sơ, cam kết", readonly=True,
                                             states={'Draft': [('readonly', False)]})
    preop_photo_shoot = fields.Boolean(string='Chụp ảnh trước phẫu thuật',
                                       help="Xác nhận khách đã được Chụp ảnh trước phẫu thuật", readonly=True,
                                       states={'Draft': [('readonly', False)]})
    preop_advise = fields.Boolean(string='Tư vấn trước phẫu thuật',
                                  help="Xác nhận khách đã được Tư vấn trước phẫu thuật", readonly=True,
                                  states={'Draft': [('readonly', False)]})

    # surgical_wound = fields.Selection(SURGICAL_WOUND, string='Surgical Wound', readonly=True,
    #                                   states={'Draft': [('readonly', False)]})
    info = fields.Text(string='Extra Info', readonly=True,
                       states={'Draft': [('readonly', False)], 'Confirmed': [('readonly', False)],
                               'In Progress': [('readonly', False)]})
    anesthesia_report = fields.Text(string='Anesthesia Report', readonly=True,
                                    states={'Draft': [('readonly', False)], 'Confirmed': [('readonly', False)],
                                            'In Progress': [('readonly', False)]})
    institution = fields.Many2one('sh.medical.health.center', string='Health Center', help="Health Center",
                                  required=True, readonly=False,
                                  states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    # postoperative_dx = fields.Many2one('sh.medical.pathology',
    #                                    string='Post-op dx',
    #                                    help="Post-operative diagnosis",
    #                                    readonly=True, states={'Draft': [('readonly', False)]})
    surgery_team = fields.One2many('sh.medical.surgery.team', 'name', string='Team Members',
                                   help="Professionals Involved in the surgery", readonly=False,
                                   states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    supplies = fields.One2many('sh.medical.surgery.supply', 'name', string='Supplies',
                               help="List of the supplies required for the surgery", readonly=False,
                               states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    # medicines = fields.One2many('sh.medical.surgery.medicines', 'name', string='Supplies', help="List of the medicines required for the surgery", readonly=True, states={'In Progress': [('readonly', False)]})
    # building = fields.Many2one('sh.medical.health.center.building', string='Building', help="Building of the selected Health Center", required=True, readonly=True, states={'Draft': [('readonly', False)]})
    department = fields.Many2one('sh.medical.health.center.ward', string='Department',
                                 domain="[('institution','=',institution),('type','=','Surgery')]",
                                 help="Department of the selected Health Center", required=True, readonly=False,
                                 states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    department_type = fields.Selection(related="department.type", store=True, depends=['department'])
    # department = fields.Many2one('sh.medical.health.center.ward', string='Department', help="Department of the selected Health Center", domain=[('institution', '=', institution)],required=True, readonly=True, states={'Draft': [('readonly', False)]})
    operating_room = fields.Many2one('sh.medical.health.center.ot', string='Operation Theater',
                                     domain="[('department','=',department)]", readonly=False,
                                     states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    state = fields.Selection(STATES, string='State', readonly=True, default=lambda *a: 'Draft', tracking=True)

    other_bom = fields.Many2many('sh.medical.product.bundle', 'sh_surgery_bom_rel', 'surgery_id', 'bom_id',
                                 string='All BOM of service',
                                 domain="[('service_id', 'in', services),('region', '=', region),('type', '=', 'Surgery')]")

    surgical_diagram = fields.Html('Lược đồ phẫu thuật', readonly=False,
                                   states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    surgical_order = fields.Text('Trình tự phẫu thuật', readonly=False,
                                 states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    anesthetist_type = fields.Selection(PP_VO_CAM,
                                        'Phương pháp vô cảm', readonly=False,
                                        states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    anesthetist_type_value = fields.Char('Giá trị phương pháp vô cảm', compute='set_value_anesthetist_type')

    @api.depends('anesthetist_type')
    def set_value_anesthetist_type(self):
        PP_VO_CAM_DICT = {'te_tai_cho': 'Tê tại chỗ',
                          'te_me_co_thu_phi': 'Tiền mê có thu phí',
                          'te_me_theo_chi_dinh_bac_sy': 'Tiền mê theo chỉ định bác sỹ',
                          'me_tinh_mach': 'Mê tĩnh mạch',
                          'gay_te_tuy_song': 'Gây tê tủy sống',
                          'gay_me_mask_thanh_quan': 'Gây mê mask thanh quản',
                          'gay_me_nkq_duoi_4_h': 'Gây mê NKQ < 4 giờ',
                          'gay_me_nkq_tren_4_h': 'Gây mê NKQ > 4 giờ',
                          'te_tai_cho_mask_tq': 'Tê tại chỗ + Mask TQ',
                          'te_tai_cho_me_nkq_duoi_4h': 'Tê tại chỗ + Mê NKQ < 4 h',
                          'te_tai_cho_me_nkq_tren_4h': 'Tê tại chỗ + Mê NKQ > 4 h',
                          'tien_me_te_tai_cho_mask_tq': 'Tiền mê + Tê tại chỗ + mask TQ',
                          'tien_me_te_tai_cho_me_nkq_duoi_4h': 'Tiền mê + Tê tại chỗ + Mê NKQ < 4h',
                          'tien_me_te_tai_cho_me_nkq_tren_4h': 'Tiền mê + Tê tại chỗ + Mê NKQ > 4h',
                          'te': 'Gây tê',
                          'tien_me': 'Tiền mê',
                          'me': 'Gây mê'}
        for rec in self:
            if rec.anesthetist_type:
                rec.anesthetist_type_value = PP_VO_CAM_DICT[rec.anesthetist_type]

    surgery_type = fields.Selection([('DB', 'Đặc biệt'), ('1', 'I'), ('2', 'II'), ('3', 'III')],
                                    'Loại', readonly=False,
                                    states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})

    #  check công ty hiện tại của người dùng với công ty của phiếu
    check_current_company = fields.Boolean(string='Cty hiện tại', compute='_check_current_company')

    #  domain vật tư và thuốc theo kho của phòng
    supply_domain = fields.Many2many('sh.medical.medicines', string='Supply domain', compute='_get_supply_domain')

    # trường ghi nhận phiếu được chỉ định thêm ngoài cấu hình
    is_new_request = fields.Boolean(string='Là chỉ định thêm',
                                    help="Phiếu được chỉ định thêm",
                                    default=False)

    # vùng miền
    region = fields.Selection(REGION, string='Miền', help="Vùng miền", related="institution.region")

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #',
                             required=True, readonly=True,
                             ondelete='cascade')

    services_domain = fields.Many2many('sh.medical.health.center.service',
                                       related='walkin.service',
                                       string="Services Domain")
    allow_institutions = fields.Many2many('sh.medical.health.center',
                                          string='Allow institutions',
                                          related='walkin.allow_institutions')

    # Lưu lại để truy xuất nhanh hơn
    booking_id = fields.Many2one('crm.lead', related='walkin.booking_id', store=True)
    code_booking = fields.Char(string='Mã booking tương ứng', related='booking_id.name', store=True)

    # Áp dụng rule Phiếu PTTT - share company
    company_id = fields.Many2one('res.company', related='booking_id.company_id',
                                 string='Company',
                                 store=True,
                                 readonly=True,
                                 ondelete='cascade')
    company2_id = fields.Many2many('res.company', 'sh_medial_surgery_company_related_rel', 'surgery_id', 'company_id',
                                   related='booking_id.company2_id',
                                   store=True,
                                   readonly=True,
                                   ondelete='cascade')

    @api.onchange('walkin')
    def get_service(self):
        self.services = False
        if self.walkin:
            self.services = [(6, 0, self.walkin.service.filtered(lambda s: not s.is_no_specialty).ids)]

    def action_cancelled(self):
        if self.state != 'Draft':
            raise ValidationError('Bạn chỉ có thể hủy khi phiếu ở trạng thái NHÁP')
        else:
            self.state = 'Cancelled'

    # Tự động chọn BOM theo dịch vụ (Phiếu PTTT)
    @api.onchange('services')
    def get_default_other_bom(self):
        self.other_bom = False
        if self.services:
            list_result = []
            for service in self.services:
                other_bom = self.env['sh.medical.product.bundle'].search(
                    [('service_id', '=', service._origin.id), ('type', '=', 'Surgery'), ('region', '=', self.region)],
                    limit=1)
                if other_bom:
                    list_result.append(other_bom.id)
            self.other_bom = [(6, 0, list_result)]

    @api.depends('institution.his_company')
    def _check_current_company(self):
        for record in self:
            record.check_current_company = True if record.institution.his_company == self.env.company else False

    @api.depends('operating_room')
    def _get_supply_domain(self):
        for record in self:
            record.supply_domain = False
            room = record.operating_room
            if room:
                # TODO refactor nhanh
                locations = room.location_medicine_stock + room.location_supply_stock
                if locations:
                    products = self.env['stock.quant'].search(
                        [('quantity', '>', 0), ('location_id', 'in', locations.ids)]).filtered(
                        lambda q: q.reserved_quantity < q.quantity).mapped('product_id')
                    if products:
                        medicines = self.env['sh.medical.medicines'].search([('product_id', 'in', products.ids)])
                        record.supply_domain = [(6, 0, medicines.ids)]

    @api.onchange('date_requested', 'surgery_date', 'surgery_end_date')
    def _onchange_date_surgery(self):
        if self.surgery_date and self.date_requested and self.surgery_end_date:
            if self.surgery_date < self.date_requested or self.surgery_date > self.surgery_end_date:
                raise UserError(
                    _('Thông tin không hợp lệ! Ngày giờ phẫu thuật phải sau ngày giờ chỉ định và trước ngày kết thúc phẫu thuật!'))

    # cộng dồn số lượng vật tư nếu đã nhập rồi
    # map cả dịch vụ thực hiện
    @api.onchange('supplies')
    def _onchange_supplies(self):
        if self.supplies:
            id_supplies = {}
            inx = 0
            for supply in self.supplies:
                if str(supply.supply.id) in id_supplies:
                    # cộng dồn số lượng
                    qty_sup = self.supplies[id_supplies[str(supply.supply.id)]].qty_used + supply.qty_used
                    self.supplies[id_supplies[str(supply.supply.id)]].qty_used = qty_sup
                    self.supplies = [(2, supply.id, False)]
                else:
                    # chưa có
                    id_supplies[str(supply.supply.id)] = inx
                inx += 1

    def write(self, vals):
        res = super(SHealthSurgery, self).write(vals)
        for record in self.with_env(self.env(su=True)):
            # CASE ĐỔI CHI NHÁNH THỰC HIỆN: Cập nhật lại công ty ở SO để ghi nhận doanh thu cho cơ sở thự hiện
            if vals.get('institution'):
                institution_detail = self.env['sh.medical.health.center'].browse(vals.get('institution'))
                # lấy kho của công ty
                ins_warehouse = self.env['stock.warehouse'].with_env(self.env(su=True)).search(
                    [('company_id', '=', institution_detail.his_company.id)], limit=1)
                if not ins_warehouse:
                    raise ValidationError(_('Công ty bạn chọn không có kho hàng!'))
                # record.walkin.sale_order_id.warehouse_id = ins_warehouse.id
                # record.walkin.sale_order_id.company_id = institution_detail.his_company.id
                record.walkin.sale_order_id.write(
                    {'company_id': institution_detail.his_company.id, 'warehouse_id': ins_warehouse.id})

            if vals.get('date_requested') or vals.get('surgery_date') or vals.get('surgery_end_date'):
                date_requested = vals.get('date_requested') or record.date_requested
                surgery_date = vals.get('surgery_date') or record.surgery_date
                surgery_end_date = vals.get('surgery_end_date') or record.surgery_end_date

                # format to date
                if isinstance(date_requested, str):
                    date_requested = datetime.datetime.strptime(date_requested, '%Y-%m-%d %H:%M:%S')
                if isinstance(surgery_date, str):
                    surgery_date = datetime.datetime.strptime(surgery_date, '%Y-%m-%d %H:%M:%S')
                if isinstance(surgery_end_date, str):
                    surgery_end_date = datetime.datetime.strptime(surgery_end_date, '%Y-%m-%d %H:%M:%S')

                if surgery_date and date_requested and surgery_end_date and (
                        (surgery_date < date_requested) or (surgery_date > surgery_end_date)):
                    raise UserError(
                        _('Thông tin không hợp lệ! Ngày giờ phẫu thuật phải sau ngày giờ chỉ định và trước ngày kết thúc phẫu thuật!'))

            if vals.get('services'):
                # check dịch vụ đổi trong phiếu chuyên khoa: nếu xóa sẽ xóa dv sẽ xóa ở dv ở thành viên tham gia
                # thành viên tham gia
                for surgery_mem in record.surgery_team.mapped('service_performances').ids:
                    if surgery_mem not in record.services.ids:
                        record.surgery_team.write({'service_performances': [(3, surgery_mem)]})

                # vtth
                for supply_sur in record.supplies.mapped('services').ids:
                    if supply_sur not in record.services.ids:
                        record.supplies.write({'services': [(3, supply_sur)]})

            if vals.get('supplies') and record.state in ['Done', 'Signed']:
                raise ValidationError('Phiếu đã hoàn thành bạn không thể chỉnh sửa VTTH')

        return res

    def view_detail_surgery(self):
        return {
            'name': 'Chi tiết Phẫu thuật - Thủ thuật',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_surgery_view').id,
            'res_model': 'sh.medical.surgery',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
            # 'context': {},
            'res_id': self.id
        }

    @api.onchange('operating_room', 'other_bom')
    def _onchange_other_bom(self):
        self.supplies = False
        if self.other_bom:

            vals = []
            check_duplicate = []
            for record in self.other_bom:
                for record_line in record.products.filtered(lambda p: p.note == 'Surgery'):
                    location = self.operating_room.location_supply_stock
                    if record_line.product_id.medicament_type == 'Medicine':
                        location = self.operating_room.location_medicine_stock
                    # product = record_line.product_id.product_id  # product.product
                    if location:
                        # available_qty = self.env['stock.quant']._get_available_quantity(product_id=product, location_id=location)
                        # if record_line.uom_id != product.uom_id:
                        #     available_qty = product.uom_id._compute_quantity(available_qty, record_line.uom_id)
                        # qty = min(record_line.quantity, available_qty)
                        qty = record_line.quantity
                        # if qty > 0:
                        mats_id = record_line.product_id.id
                        if mats_id not in check_duplicate:
                            check_duplicate.append(mats_id)
                            vals.append((0, 0, {'supply': mats_id,
                                                'qty': qty,
                                                'qty_used': qty,
                                                'uom_id': record_line.uom_id.id,
                                                'location_id': location.id,
                                                'services': [(4, record.service_id.id)],
                                                'notes': ''}))
                        else:
                            old_supply_index = check_duplicate.index(mats_id)
                            vals[old_supply_index][2]['services'].append((4, record.service_id.id))
                            vals[old_supply_index][2]['qty'] += qty
                            vals[old_supply_index][2]['qty_used'] += qty

            self.supplies = vals
            # Đây là phần tính trung bình số lượng sử dụng theo số dịch vụ
            for supply in self.supplies:
                if supply.uom_id.int_rounding:
                    supply.qty_used = round(supply.qty_used / len(supply.services))
                    supply.qty = round(supply.qty / len(supply.services))
                else:
                    supply.qty_used = supply.qty_used / len(supply.services)
                    supply.qty = supply.qty / len(supply.services)

    @api.onchange('institution')
    def _onchange_institution(self):
        # set khoa mac dinh la khoa phau thuat cua co so y te
        if self.institution:
            sur_dep = self.env['sh.medical.health.center.ward'].search(
                [('institution', '=', self.institution.id), ('type', '=', 'Surgery')], limit=1)
            self.department = sur_dep
            self.operating_room = False

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.surgery.%s' % vals['institution'])
        if not sequence:
            raise ValidationError(_('Định danh phiếu PTTT của Cơ sở y tế này đang không tồn tại!'))
        vals['name'] = sequence
        return super(SHealthSurgery, self).create(vals)

    def action_surgery_confirm(self):
        # for surgery in self:
        #     #cap nhat tinh trang phong mo da dươc đặt trước
        #     if surgery.operating_room:
        #         query = _("update sh_medical_health_center_ot set state='Reserved' where id=%s")%(str(surgery.operating_room.id))
        #         self.env.cr.execute(query)

        if self.sudo().walkin.state == 'WaitPayment':
            raise ValidationError(
                _('Bạn không thể xác nhận phiếu do Phiếu Khám liên quan của phiếu này chưa thu đủ tiền làm dịch vụ!'))

        # Tự động chọn BOM theo dịch vụ
        if self.services:
            list_result = []
            for service in self.services:
                other_bom = self.env['sh.medical.product.bundle'].search(
                    [('service_id', '=', service._origin.id), ('type', '=', 'Surgery'), ('region', '=', self.region)],
                    limit=1)
                if other_bom:
                    list_result.append(other_bom.id)
            self.other_bom = [(6, 0, list_result)]
            self._onchange_other_bom()

        # nếu chưa có vtth được nhập thì đổ bom theo cấu hình
        if not self.supplies:
            # add vat tu tieu hao ban dau cho pttt
            sg_data = []
            check_duplicate = []
            # self.supplies = False => GIỮ LẠI VTTH ĐÃ NHẬP TRC ĐÓ

            for ser in self.services:
                # add vat tu tieu hao tong - ban dau
                for mats in ser.material_ids.filtered(lambda m: m.note == 'Surgery'):
                    location = self.operating_room.location_supply_stock
                    if mats.product_id.medicament_type == 'Medicine':
                        location = self.operating_room.location_medicine_stock
                    product = mats.product_id.product_id  # product.product
                    if location:
                        available_qty = self.env['stock.quant']._get_available_quantity(product_id=product,
                                                                                        location_id=location)
                        if mats.uom_id != product.uom_id:
                            available_qty = product.uom_id._compute_quantity(available_qty, mats.uom_id)
                        qty = min(mats.quantity, available_qty)
                        # if qty > 0:
                        mats_id = mats.product_id.id
                        if mats_id not in check_duplicate:
                            check_duplicate.append(mats_id)
                            sg_data.append((0, 0, {'supply': mats_id,
                                                   'qty': mats.quantity,
                                                   'qty_used': qty,
                                                   'uom_id': mats.uom_id.id,
                                                   'location_id': location.id,
                                                   'services': [(4, ser.id)],
                                                   'notes': mats.note}))
                        else:
                            old_supply_index = check_duplicate.index(mats_id)
                            sg_data[old_supply_index][2]['services'] += [(4, ser.id)]
                            sg_data[old_supply_index][2]['qty'] += mats.quantity
                            sg_data[old_supply_index][2]['qty_used'] = min(
                                qty + sg_data[old_supply_index][2]['qty_used'],
                                available_qty)

            return self.write({'state': 'Confirmed', 'supplies': sg_data, 'surgery_date': fields.Datetime.now(),
                               'surgery_end_date': fields.Datetime.now() + timedelta(hours=2)})
        else:
            return self.write({'state': 'Confirmed'})

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

                # check chính xác tại tủ xuất
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

    def action_surgery_start(self):
        # mở lại phiếu
        if self.state == 'Done':
            self.reverse_materials()
            self.sudo().walkin.update_walkin_material(mats_types=['Surgery'])
            res = self.write({'state': 'In Progress'})
        else:
            # for surgery in self:
            #     if surgery.operating_room:
            #         query = _("update sh_medical_health_center_ot set state='Occupied' where id=%s")%(str(surgery.operating_room.id))
            #         self.env.cr.execute(query)

            if self.surgery_date:
                surgery_date = self.surgery_date
            else:
                surgery_date = datetime.datetime.now()

            res = self.write({'state': 'In Progress', 'surgery_date': surgery_date})

        # update so pttt hoan thanh
        # Walkin = self.env['sh.medical.appointment.register.walkin'].sudo().browse(self.sudo().walkin.id)
        # Walkin.write({'surgery_done_count': self.env['sh.medical.surgery'].search_count(
        #     [('walkin', '=', self.sudo().walkin.id), ('state', '=', 'Done')])})

        # return res

    # def action_surgery_cancel(self):
    #     # for surgery in self:
    #     #     if surgery.operating_room:
    #     #         query = _("update sh_medical_health_center_ot set state='Free' where id=%s")%(str(surgery.operating_room.id))
    #     #         self.env.cr.execute(query)
    #     self.write({'state': 'Cancelled'})

    def action_surgery_set_to_draft(self):
        self.other_bom = False
        self.supplies = False
        self.write({'state': 'Draft'})

    def action_surgery_end(self):
        self.ensure_one()
        if len(self.other_bom) != len(self.services):
            raise ValidationError('Số lượng BOM phải bằng số lượng dịch vụ')
        if self.surgery_end_date > datetime.datetime.now():
            raise ValidationError('Bạn không thể đóng phiếu do thời gian kết thúc lớn hơn thời gian hiện tại')
        if not self.operating_room.non_manage_material:
            if not self.supplies:
                raise ValidationError('Bạn phải nhập VTTH cho phiếu trước khi xác nhận hoàn thành!')
            if not self.surgery_team:
                raise ValidationError('Bạn cần nhập Thành viên tham gia trước khi xác nhận hoàn thành')

        # for surgery in self:
        #     if surgery.operating_room:
        #         query = _("update sh_medical_health_center_ot set state='Free' where id=%s")%(str(surgery.operating_room.id))
        #         self.env.cr.execute(query)

        # tru vat tu theo tieu hao của phiếu khám phâu thuật thủ thuật
        dept = self.department
        if self.surgery_end_date:
            surgery_end_date = self.surgery_end_date
        else:
            surgery_end_date = fields.Datetime.now()

        # 20220320 - tungnt - onnet
        default_production_location = self.env['stock.location'].get_default_production_location_per_company()

        vals = {}
        validate_str = ''
        for mat in self.supplies:
            if mat.qty_used > 0:  # CHECK SO LUONG SU DUNG > 0
                quantity_on_hand = self.env['stock.quant']._get_available_quantity(mat.supply.product_id,
                                                                                   mat.location_id)  # check quantity trong location
                # print(mat.supply.name)
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
                        'date': surgery_end_date,
                        'company_id': self.env.company.id,
                        'date_expected': surgery_end_date,
                        # 'date_done': surgery_end_date,
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
            # picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
            #                                                       ('warehouse_id', '=',
            #                                                        self.env.ref('stock.warehouse0').id)],
            #                                                      limit=1).id
            for location_key in vals:
                pick_note = 'THBN - %s - %s - %s' % (self.name, self.sudo().walkin.name, location_key)
                pick_vals = {'note': pick_note,
                             'origin': pick_note,
                             'partner_id': self.patient.partner_id.id,
                             'patient_id': self.patient.id,
                             'picking_type_id': picking_type,
                             'location_id': int(location_key),
                             'location_dest_id': default_production_location.id,
                             'date_done': surgery_end_date,
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

                # TU DONG XÁC NHẬN XUAT KHO
                stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
                for move_line in stock_picking.move_ids_without_package:
                    for move_live_detail in move_line.move_line_ids:
                        move_live_detail.qty_done = move_live_detail.product_uom_qty
                    # move_line.quantity_done = move_line.product_uom_qty
                stock_picking.with_context(
                    force_period_date=surgery_end_date).sudo().button_validate()  # ham tru product trong inventory, sudo để đọc stock.valuation.layer

                # sua ngay hoan thanh
                for move_line in stock_picking.move_ids_without_package:
                    move_line.move_line_ids.write({'date': surgery_end_date})  # sửa ngày hoàn thành ở stock move line
                stock_picking.move_ids_without_package.write(
                    {'date': surgery_end_date})  # sửa ngày hoàn thành ở stock move
                stock_picking.date_done = surgery_end_date

                stock_picking.create_date = self.surgery_date

                # Cập nhật ngược lại picking_id vào mats để truyền số liệu sang vật tư phiếu khám
                self.supplies.filtered(lambda s: s.location_id.id == int(location_key)).write(
                    {'picking_id': stock_picking.id})

        elif validate_str != '':
            raise ValidationError(
                _("Các loại Thuốc và Vật tư sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))

        res = self.write({'state': 'Done', 'surgery_end_date': surgery_end_date})

        # cap nhat vat tu cho phieu kham
        self.sudo().walkin.update_walkin_material(mats_types=['Surgery'])

        # tạo đơn thuốc mang về cho bệnh nhân theo BOM dịch vụ
        # prescription_wakin = []
        # prescription_line = []
        # flag_pres = False
        # for service_done in self.services:
        #     if service_done.prescription_ids:
        #         flag_pres = True
        #         for prescription in service_done.prescription_ids:
        #             prescription_line.append((0, 0, {
        #                 'name': prescription.product_id.id,
        #                 'patient': self.patient.id,
        #                 'qty': prescription.qty,
        #                 'dose': prescription.dose,
        #                 'dose_unit_related': prescription.dose_unit,
        #                 'common_dosage': prescription.common_dosage.id,
        #                 'duration': prescription.duration,
        #                 'duration_period': prescription.duration_period,
        #                 'info': service_done.name}))
        #
        # if flag_pres:
        #     if len(self.walkin.prescription_ids) > 0:
        #         prescription_wakin = self.walkin.prescription_ids[0]
        #         prescription_wakin.prescription_line = prescription_line
        #     else:
        #         # lấy thông tin tủ kê đơn của bệnh viện
        #         print(self.institution.location_medicine_stock.name)
        #         prescription_wakin.append((0, 0, {
        #             'patient': self.patient.id,
        #             'date': surgery_end_date,
        #             'doctor': self.surgeon.id,
        #             'location_id': self.institution.location_medicine_stock.id,
        #             'walkin': self.walkin.id,
        #             'prescription_line': prescription_line,
        #             'state': 'Draft'}))
        #
        # self.walkin.write({'prescription_ids': prescription_wakin})
        # print(prescription_wakin)
        # print(self.services)

        # # log access patient
        # data_log = self.env['sh.medical.patient.log'].search([('walkin', '=', self.walkin.id)])
        # data_ck = False
        # for data in data_log:
        #     # nếu đã có data log cho ck khoa này rồi
        #     if data.department.id == self.department.id:
        #         data_ck = data
        #     # nếu có log khoa KB rồi thì cập nhật ngày ra cho khoa kb là ngày bắt đầu làm dịch vụ
        #     if data.department.type == 'Examination':
        #         data.date_out = self.surgery_date
        # # nếu chưa có data log=> tạo log
        # if not data_ck:
        #     vals_log = {'walkin': self.walkin.id,
        #                 'patient': self.patient.id,
        #                 'department': self.department.id,
        #                 'date_in': self.surgery_date,
        #                 'date_out': self.surgery_end_date}
        #     self.env['sh.medical.patient.log'].create(vals_log)
        # else:
        #     data_ck.date_in = self.surgery_date
        #     data_ck.date_out = self.surgery_end_date

        # update so pttt hoan thanh
        Walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.sudo().walkin.id)
        Walkin.sudo().write({'surgery_done_count': self.env['sh.medical.surgery'].search_count(
            [('walkin', '=', self.sudo().walkin.id), ('state', '=', 'Done')])})
        # return res

    def action_surgery_sign(self):
        phy_obj = self.env["sh.medical.physician"]
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = phy_obj.search(domain)
        if user_ids:
            self.signed_by = self.env.uid or False
            self.state = 'Signed'
        else:
            raise UserError(_('No physician associated to logged in user'))

    def unlink(self):
        for surgery in self.filtered(lambda sg: sg.state not in ['Draft']):
            # raise UserError(_('You can not delete a record that is already been signed !!'))
            raise UserError(_('Bạn không thể xóa Phiếu PTTT khi phiếu đang không ở trạng thái Nháp!'))
        return super(SHealthSurgery, self).unlink()

    def reset_all_supply(self):
        for surgery in self.filtered(lambda sg: sg.state not in ['Draft', 'Done', 'Signed']):
            surgery.supplies = False

    def add_inpatient(self):
        res = self.env['sh.medical.inpatient'].create({
            'walkin': self.env.context.get('default_walkin'),
            'admission_reason': self.env.context.get('default_admission_reason'),
            'admission_type': self.env.context.get('default_admission_type'),
            'patient': self.env.context.get('default_patient'),
            'operating_physician': self.env.context.get('default_operating_physician'),
            'attending_physician': self.env.context.get('default_attending_physician'),
            'services': self.env.context.get('default_services'),
            'institution': self.env.context.get('default_institution'),
        })

        return {
            'name': _('Chi tiết phiếu lưu bệnh nhân'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_inpatient_view').id,
            'res_model': 'sh.medical.inpatient',  # model want to display
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': res.id
        }

    # ACTION XUAT BENH AN TOM TAT
    def action_report_benh_an_tom_tat(self):
        surgery_attacment = self.env.ref('shealth_all_in_one.benhantomtat_report_attachment')
        decode = base64.b64decode(surgery_attacment.datas)
        doc = MailMerge(BytesIO(decode))
        # gia tri tra ve
        data_list = []
        for record in self:
            # convert date and time into user timezone
            timezone = self._context.get('tz') or self.env.user.partner_id.tz or 'UTC'

            # convert date and time into user timezone
            self_tz = self.with_context(tz=timezone)
            # local_tz = pycompat.to_native(self._context.get('tz') or self.env.user.partner_id.tz or 'UTC')# make safe for str{p,f}time()

            record_data = {}
            record_data['TEN_CTY'] = str(record.institution.his_company.name).upper()
            record_data['TEN_BV'] = str(record.institution.name).upper()
            record_data['TEN_BN'] = record.patient.name
            record_data['GIOI_TINH'] = str(
                dict(record.patient._fields['gender']._description_selection(self.env)).get(record.patient.gender))
            record_data['AGE'] = record.patient.age
            record_data['DOB'] = record.patient.birth_date.strftime('%d/%m/%Y') if record.patient.birth_date else ''
            record_data['DAN_TOC'] = record.patient.ethnic_group.name
            record_data['NGOAI_KIEU'] = record.patient.foreign.name
            dia_chi = ''
            if record.patient.street:
                dia_chi += record.patient.street
            if record.patient.state_id:
                dia_chi += ', ' + record.patient.state_id.name
            if record.patient.country_id:
                dia_chi += ', ' + record.patient.country_id.name
            record_data['DIA_CHI'] = dia_chi

            record_data['NGUOI_THAN'] = ''
            # NGUOI THAN
            family = record.patient.family
            if len(family) > 0:
                family = family[0]
                if family.type_relation and family.name and family.address:
                    record_data['NGUOI_THAN'] = family.type_relation.name + " - " + str(family.name) + " - " + str(
                        family.address)

            # NGAY KHAM
            date = fields.Datetime.context_timestamp(self_tz, fields.Datetime.from_string(record.walkin.date))
            record_data['NGAY_KHAM'] = pycompat.to_text(date.strftime("%H giờ %M phút   ngày %d tháng %m năm %Y."))
            record_data['LY_DO_KHAM'] = record.walkin.reason_check
            record_data['NGHE_NGHIEP'] = record.patient.function
            record_data['QUA_TRINH_BENH_LY'] = record.walkin.pathological_process
            record_data['TS_NGOAIKHOA'] = record.walkin.surgery_history
            record_data['TS_NOIKHOA'] = record.walkin.medical_history
            record_data['TS_DIUNG'] = record.walkin.allergy_history
            record_data['TS_GIADINH'] = record.walkin.family_history
            record_data['TOAN_THAN'] = record.walkin.physical_exam
            record_data['TUAN_HOAN'] = record.walkin.cyclic_info
            record_data['HO_HAP'] = record.walkin.respiratory_exam
            record_data['TIEU_HOA'] = record.walkin.digest_exam
            record_data['THAN_TIET_NIEU'] = record.walkin.reins_exam
            record_data['THAN_KINH'] = record.walkin.nerve_exam
            record_data['CO_QUAN_KHAC'] = record.walkin.other_exam
            record_data['CHUYEN_KHOA'] = record.walkin.specialty_exam
            record_data['MACH'] = record.walkin.bpm
            record_data['NHIET_DO'] = record.walkin.temperature
            record_data['HUYET_AP'] = str(record.walkin.systolic) + '/' + str(record.walkin.diastolic)
            record_data['NHIP_THO'] = record.walkin.respiratory_rate
            record_data['CAN_NANG'] = record.walkin.weight
            record_data['CHIEU_CAO'] = record.walkin.height
            if record.patient.blood_type:
                record_data['HUYET_HOC'] = '- Nhóm máu: ' + str(record.patient.blood_type) + str(
                    record.patient.rh) + "\n"
            # KET QUA BAT THUONG - CAN LAM SANG
            can_lam_sang = ''
            labtest_abnomal = record.walkin.lab_test_ids.filtered(lambda l: l.abnormal)
            if len(labtest_abnomal) > 0:
                can_lam_sang = 'Các XN có chỉ số bất thường: '
                for lt in labtest_abnomal:
                    if lt.has_child:
                        can_lam_sang += "\n+ " + str(lt.test_type.name) + ":"
                        for lt_case_ab in lt.lab_test_criteria.filtered(lambda la: la.abnormal):
                            can_lam_sang += "\n- " + str(lt_case_ab.name) + ": " + str(lt_case_ab.result) + (
                                str(lt_case_ab.units.name) if lt_case_ab.units else '')
                    else:
                        can_lam_sang += "\n+ " + str(lt.test_type.name) + ": " + str(lt.results)
            else:
                can_lam_sang = '\nKết quả kiểm tra không có gì bất thường.'

            record_data['CAN_LAM_SANG'] = can_lam_sang
            record_data['CHUAN_DOAN_BAN_DAU'] = record.walkin.info_diagnosis
            record_data['DICH_VU'] = ';'.join(map(str, record.services.mapped('name')))
            # THUOC TIEU HAO
            # thuoc_tieu_hao = ''
            # medicines = record.walkin.material_ids.filtered(lambda m: m.product_id.medicament_type == 'Medicine')
            # if len(medicines) > 0:
            #     thuoc_tieu_hao = '\n- Thuốc: '
            #     for medicine in medicines:
            #         thuoc_tieu_hao += "\n + " + str(medicine.product_id.name) + ": " + str(medicine.quantity) + " " + str(medicine.uom_id.name)+ " (" + str(dict(medicine._fields['note']._description_selection(self.env)).get(medicine.note))+")"
            # record_data['THUOC_TIEU_HAO'] = thuoc_tieu_hao
            record_data['CHUAN_DOAN_RA_VIEN'] = 'Sau ' + ';'.join(map(str, record.services.mapped('name'))) + '.'
            if record.walkin.date_out:
                date_out = fields.Datetime.context_timestamp(self_tz,
                                                             fields.Datetime.from_string(record.walkin.date_out))
                ngay_ra_vien = pycompat.to_text(date.strftime("%d/%m/%Y")) + " đến ngày " + pycompat.to_text(
                    date_out.strftime("%d/%m/%Y."))
            else:
                ngay_ra_vien = ''
            record_data['NGAY_RA_VIEN'] = ngay_ra_vien

        data_list.append(record_data)
        doc.merge_templates(data_list, separator='page_break')

        fp = BytesIO()
        doc.write(fp)
        doc.close()
        fp.seek(0)
        report = base64.encodebytes((fp.read()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({'name': 'BENH_AN_TOM_TAT.docx',
                                                              'datas': report,
                                                              'res_model': 'temp.creation',
                                                              'public': True})

        return {'name': 'BỆNH ÁN TÓM TẮT',
                'type': 'ir.actions.act_window',
                'res_model': 'temp.wizard',
                'view_mode': 'form',
                'target': 'inline',
                'view_id': self.env.ref('ms_templates.report_wizard').id,
                'context': {'attachment_id': attachment.id}
                }

    # ẨN NÚT THEO STATE PHIẾU
    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(SHealthSurgery, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                            submenu=submenu)
    #     doc = etree.XML(res['arch'])
    #
    #     # for t in doc.xpath("//" + view_type):
    #     #     t.attrib['delete'] = 'false'
    #     #     t.attrib['duplicate'] = 'false'
    #     # res['arch'] = etree.tostring(doc, encoding='unicode')
    #
    #     res['arch'] = etree.tostring(doc, encoding='unicode')
    #     return res


# Inheriting Patient module to add "Surgeries" screen reference
class SHealthPatient(models.Model):
    _inherit = 'sh.medical.patient'
    pediatrics_surgery_ids = fields.One2many('sh.medical.surgery', 'patient', string='Surgeries')


#
# class SHealthSpecialtyTeam(models.Model):
#     _name = "sh.medical.specialty.team"
#     _description = "Specialty Team"
#
#     # def get_domain_physician(self):
#     #     if self.env.ref('shealth_all_in_one.11',False) and self.env.ref('shealth_all_in_one.51',False):
#     #         return [('is_pharmacist', '=', False), ('speciality', 'in', [self.env.ref('shealth_all_in_one.11').id,self.env.ref('shealth_all_in_one.51').id])]
#     #     elif self.env.ref('shealth_all_in_one.11',False):
#     #         return [('is_pharmacist', '=', False), ('speciality', 'in', [self.env.ref('shealth_all_in_one.11').id])]
#     #     elif self.env.ref('shealth_all_in_one.51',False):
#     #         return [('is_pharmacist', '=', False), ('speciality', 'in', [self.env.ref('shealth_all_in_one.51').id])]
#     #     else:
#     #         return [('is_pharmacist', '=', False)]
#     #
#     # def get_domain_nurse(self):
#     #     if self.env.ref('shealth_all_in_one.33', False):
#     #         return [('is_pharmacist', '=', False), ('speciality', '=', self.env.ref('shealth_all_in_one.33').id)]
#     #     else:
#     #         return [('is_pharmacist', '=', False)]
#
#     # name = fields.Many2one('sh.medical.specialty', string='Specialty')
#     # doctor_member = fields.Many2many('sh.medical.physician', 'sh_specialty_doctor_rel', 'surgery_id', 'doctor_id',
#     #                  string='Doctor'
#     #                                  # , domain=lambda self:self.get_domain_physician()
#     #                                  )
#     # physician_member = fields.Many2many('sh.medical.physician', 'sh_specialty_nursing_rel', 'surgery_id', 'physician_id',
#     #                                  string='Physician member',required=True
#     #                                     # , domain=lambda self:self.get_domain_nurse()
#     #                                     )
#     # service_performance = fields.Many2one('sh.medical.health.center.service', string='Service',
#     #                               help="Service that persons participated on this specialty", required=True)
#     # notes = fields.Char(string='Notes')
#
#     _sql_constraints = [('name_unique', 'unique(name,team_member,service_performances,role)',
#                          "Vai trò của thành viên với dịch vụ phải là duy nhất!")]
#
#     @api.constrains('name', 'team_member', 'service_performances', 'role')
#     def _check_constrains_team_member(self):
#         for rec in self:
#             similars = self.env['sh.medical.specialty.team'].search(
#                 [('id', '!=', rec.id), ('name', '=', rec.name.id), ('team_member', '=', rec.team_member.id),
#                  ('role', '=', rec.role.id)])
#             if similars:
#                 for sim_rec in similars:
#                     for rec_service in rec.service_performances:
#                         if rec_service in sim_rec.service_performances:
#                             raise ValidationError('Vai trò của thành viên với dịch vụ phải là duy nhất!')
#
#     def get_domain_role(self):
#         if self.env.context.get('department_type'):
#             return [('type', '=', self.env.context.get('department_type').lower())]
#         else:
#             return [('type', 'in', ['spa', 'laser', 'odontology'])]
#
#     name = fields.Many2one('sh.medical.specialty', string='Specialty')
#     team_member = fields.Many2one('sh.medical.physician', string='Thành viên',
#                                   help="Health professional that participated on this surgery",
#                                   domain=[('is_pharmacist', '=', False)], required=True)
#
#     service_performance = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ thực hiện',
#                                           help="Service that persons participated on this surgery")
#
#     service_performances = fields.Many2many('sh.medical.health.center.service', 'sh_specialty_team_services_rel',
#                                             'specialty_team_id',
#                                             'service_id', string='Dịch vụ thực hiện',
#                                             help="Các dịch vụ của thành viên với vai trog này thực hiện")
#     role = fields.Many2one('sh.medical.team.role', string='Vai trò', domain=lambda self: self.get_domain_role())
#     notes = fields.Char(string='Notes')
#
#
# # CHUYEN KHOA: DA LIEU, RANG HAM MAT ...
# class SHealthSpecialtySupply(models.Model):
#     _name = "sh.medical.specialty.supply"
#     _description = "Supplies related to the services in specialty"
#
#     MEDICAMENT_TYPE = [
#         ('Medicine', 'Medicine'),
#         ('Supplies', 'Supplies'),
#     ]
#     EXPLANATION_SUPPLY = [
#         ('doctor_appointed', 'Theo y lệnh bác sĩ'),
#         ('not_in_the_bom', 'Không có trong BOM'),
#         ('other', 'Khác'),
#     ]
#
#     name = fields.Many2one('sh.medical.specialty', string='Specialty')
#     qty = fields.Float(string='Initial required quantity', digits='Product Unit of Measure', required=True,
#                        help="Initial required quantity", default=lambda *a: 0)
#     uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
#     supply = fields.Many2one('sh.medical.medicines', string='Supply', required=True,
#                              help="Supply to be used in this services in specialty", domain=lambda self: [
#             ('categ_id', 'child_of', self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
#     notes = fields.Char(string='Notes')
#     explanation_supply = fields.Selection(EXPLANATION_SUPPLY, string='Giải trình')
#     is_diff_bom = fields.Boolean('Khác định mức?', compute='compute_qty_used_bom')
#     qty_used = fields.Float(string='Actual quantity used', digits=dp.get_precision('Product Unit of Measure'),
#                             required=True, help="Actual quantity used", default=lambda *a: 1)
#     qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
#                              compute='compute_available_qty_supply')
#     qty_in_loc = fields.Float(string='Số lượng tại tủ', required=True, help="Số lượng khả dụng trong tủ trực",
#                               compute='compute_available_qty_supply_in_location')
#     is_warning_location = fields.Boolean('Cảnh báo tại tủ', compute='compute_available_qty_supply_in_location')
#     location_id = fields.Many2one('stock.location', 'Stock location', domain="[('usage', '=', 'internal')]")
#     medicament_type = fields.Selection(MEDICAMENT_TYPE, related="supply.medicament_type", string='Medicament Type',
#                                        store=True)
#
#     services = fields.Many2many('sh.medical.health.center.service', 'sh_surgery_specialty_service_rel',
#                                 track_visibility='onchange',
#                                 string='Dịch vụ thực hiện')
#     service_related = fields.Many2many('sh.medical.health.center.service', 'sh_surgery_specialty_service_related_rel',
#                                        related="name.services",
#                                        string='Dịch vụ liên quan')
#
#     sequence = fields.Integer('Sequence',
#                               default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự
#
#     picking_id = fields.Many2one('stock.picking', string='Phiếu điều chuyển')
#
#     @api.depends('qty_used', 'qty')
#     def compute_qty_used_bom(self):
#         for record in self:
#             if record.qty_used > record.qty:
#                 record.is_diff_bom = True
#             else:
#                 record.is_diff_bom = False
#
#     @api.depends('supply', 'uom_id')
#     def compute_available_qty_supply(self):  # so luong kha dung toan vien
#         for record in self:
#             if record.supply:
#                 record.qty_avail = record.uom_id._compute_quantity(record.supply.qty_available,
#                                                                    record.supply.uom_id) if record.uom_id != record.supply.uom_id else record.supply.qty_available
#             else:
#                 record.qty_avail = 0
#
#     @api.depends('supply', 'location_id', 'qty_used', 'uom_id')
#     def compute_available_qty_supply_in_location(self):  # so luong kha dung tai tu
#         for record in self:
#             if record.supply:
#                 quantity_on_hand = self.env['stock.quant'].with_user(1)._get_available_quantity(
#                     record.supply.product_id,
#                     record.location_id)  # check quantity trong location
#
#                 record.qty_in_loc = record.uom_id._compute_quantity(quantity_on_hand,
#                                                                     record.supply.uom_id) if record.uom_id != record.supply.uom_id else quantity_on_hand
#             else:
#                 record.qty_in_loc = 0
#
#             record.is_warning_location = True if (
#                     record.qty_used > record.qty_in_loc or record.qty_in_loc == 0) else False
#
#     @api.onchange('qty_used', 'supply')
#     def onchange_qty_used(self):
#         if self.qty_used < 0 and self.supply:
#             raise UserError(_("Số lượng nhập phải lớn hơn 0!"))
#
#     # @api.depends('location_id')
#     # def name_get(self):
#     #     result = []
#     #     for record in self:
#     #         name = record.name
#     #         if self.env.context.get('show_short_name'):
#     #             name =
#     #         result.append((record.id, name))
#     #     return result
#
#     @api.onchange('supply')
#     def _change_product_id(self):
#         self.uom_id = self.supply.uom_id
#         self.services = self.name.services
#
#         domain = {'domain': {'uom_id': [('category_id', '=', self.supply.uom_id.category_id.id)]}}
#         if self.medicament_type == 'Medicine':
#             self.location_id = self.name.perform_room.location_medicine_stock.id
#             domain['domain']['location_id'] = [('location_institution_type', '=', 'medicine'),
#                                                ('company_id', '=', self.name.institution.his_company.id)]
#         elif self.medicament_type == 'Supplies':
#             self.location_id = self.name.perform_room.location_supply_stock.id
#             domain['domain']['location_id'] = [('location_institution_type', '=', 'supply'),
#                                                ('company_id', '=', self.name.institution.his_company.id)]
#         return domain
#
#     @api.onchange('uom_id')
#     def _change_uom_id(self):
#         if self.uom_id.category_id != self.supply.uom_id.category_id:
#             self.uom_id = self.supply.uom_id
#             raise Warning(
#                 _('The Supply Unit of Measure and the Material Unit of Measure must be in the same category.'))
#
#
# class SHealthSpecialty(models.Model):
#     _name = "sh.medical.specialty"
#     _description = "Services in specialty Management"
#
#     _inherit = [
#         'mail.thread']
#
#     STATES = [
#         ('Draft', 'Draft'),
#         ('Confirmed', 'Confirmed'),
#         ('In Progress', 'In Progress'),
#         ('Done', 'Done'),
#         ('Cancelled', 'Cancelled'),
#     ]
#
#     GENDER = [
#         ('Male', 'Male'),
#         ('Female', 'Female')
#     ]
#
#     WARD_TYPE = [
#         ('Examination', 'Examination'),
#         ('Laboratory', 'Laboratory'),
#         ('Imaging', 'Imaging'),
#         ('Surgery', 'Surgery'),
#         ('Inpatient', 'Inpatient'),
#         ('Spa', 'Spa'),
#         ('Laser', 'Laser'),
#         ('Odontology', 'Odontology')
#     ]
#
#     REGION = [
#         ('North', 'Miền Bắc'),
#         ('South', 'Miền Nam')
#     ]
#
#     def _get_physician(self):
#         """Return default physician value"""
#         therapist_obj = self.env['sh.medical.physician']
#         domain = [('sh_user_id', '=', self.env.uid)]
#         user_ids = therapist_obj.search(domain)
#         if user_ids:
#             return user_ids.id or False
#         else:
#             return False
#
#     def _patient_age_at_specialty(self):
#         def compute_age_from_dates(patient_dob, patient_services_date):
#             if patient_dob and patient_services_date:
#                 dob = datetime.datetime.strptime(patient_dob.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
#                 services_date = datetime.datetime.strptime(patient_services_date.strftime('%Y-%m-%d %H:%M:%S'),
#                                                            '%Y-%m-%d %H:%M:%S').date()
#                 delta = services_date - dob
#                 # years_months_days = _(str(delta.days // 365) + " years " + str(delta.days % 365) + " days")
#                 # years_months_days = _("%s tuổi %s ngày"%(str(delta.days // 365),str(delta.days%365)))
#                 years_months_days = _("%s tuổi" % (str(delta.days // 365)))
#             else:
#                 years_months_days = _("No DoB !")
#             return years_months_days
#
#         result = {}
#         for patient_data in self:
#             patient_data.computed_age = compute_age_from_dates(patient_data.patient.birth_date,
#                                                                patient_data.services_date)
#         return result
#
#     def _specialty_duration(self):
#         for sp in self:
#             if sp.services_end_date and sp.services_date:
#                 services_date = 1.0 * calendar.timegm(
#                     time.strptime(sp.services_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))
#                 services_end_date = 1.0 * calendar.timegm(
#                     time.strptime(sp.services_end_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))
#                 duration = (services_end_date - services_date) / 3600
#                 sp.services_length = duration
#             else:
#                 sp.services_length = 0
#         return True
#
#     def get_domain_physician(self):
#         if self.env.ref('shealth_all_in_one.11', False) and self.env.ref('shealth_all_in_one.51', False):
#             return [('is_pharmacist', '=', False), (
#                 'speciality', 'in',
#                 [self.env.ref('shealth_all_in_one.11').id, self.env.ref('shealth_all_in_one.51').id])]
#         elif self.env.ref('shealth_all_in_one.11', False):
#             return [('is_pharmacist', '=', False), ('speciality', 'in', [self.env.ref('shealth_all_in_one.11').id])]
#         elif self.env.ref('shealth_all_in_one.51', False):
#             return [('is_pharmacist', '=', False), ('speciality', 'in', [self.env.ref('shealth_all_in_one.51').id])]
#         else:
#             return [('is_pharmacist', '=', False)]
#
#     def get_domain_department(self):
#         institution = self.env['sh.medical.health.center'].search([('his_company', '=', self.env.company.id)], limit=1)
#         if self.env.context.get('department_type'):
#             return [('institution', '=', institution.id),
#                     ('type', 'in', [self.env.context.get('department_type'), 'Surgery'])]
#         else:
#             return [('institution', '=', institution.id), ('type', 'in', ['Spa', 'Laser', 'Odontology'])]
#
#     name = fields.Char(string='Specialty #', size=64, readonly=True, required=True, default=lambda *a: '/')
#     patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True,
#                               states={'Draft': [('readonly', False)]})
#     pathology = fields.Many2one('sh.medical.pathology', string='Condition', help="Base Condition / Reason",
#                                 readonly=True, states={'Draft': [('readonly', False)]})
#     services = fields.Many2many('sh.medical.health.center.service', 'sh_specialty_service_rel', 'specialty_id',
#                                 'service_id',
#                                 domain="[('service_department', '=', department)]", readonly=False,
#                                 states={'Completed': [('readonly', True)]}, track_visibility='onchange',
#                                 string='Services')
#     computed_age = fields.Char(compute=_patient_age_at_specialty, size=32, string='Age during services',
#                                help="Computed patient age at the moment of the services", readonly=True,
#                                states={'Draft': [('readonly', False)]})
#     gender = fields.Selection(GENDER, string='Gender', readonly=True, states={'Draft': [('readonly', False)]})
#     physician = fields.Many2one('sh.medical.physician', string='Physician', help="Physician who did the procedure",
#                                 # domain=lambda self:self.get_domain_physician(),
#                                 readonly=False, states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
#                                 default=_get_physician)
#     sub_physician = fields.Many2one('sh.medical.physician', string='Trợ thủ/Điều dưỡng phụ', readonly=False,
#                                     states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
#                                     default=_get_physician)
#     date_requested = fields.Datetime(string='Ngày giờ chỉ định', help="Ngày giờ chỉ định", readonly=False,
#                                      states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
#                                      default=lambda *a: datetime.datetime.now())
#     services_date = fields.Datetime(string='Start date & time', help="Start of the Services", readonly=False,
#                                     states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
#                                     default=lambda *a: datetime.datetime.now())
#     services_end_date = fields.Datetime(string='End date & time', help="End of the Services", readonly=False,
#                                         states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
#     services_length = fields.Float(compute=_specialty_duration, string='Duration (Hour:Minute)',
#                                    help="Length of the services", readonly=True,
#                                    states={'Draft': [('readonly', False)]})
#     description = fields.Text(string='Description', readonly=True,
#                               states={'Draft': [('readonly', False)], 'Confirmed': [('readonly', False)],
#                                       'In Progress': [('readonly', False)]})
#     info = fields.Text(string='Extra Info', readonly=True,
#                        states={'Draft': [('readonly', False)], 'Confirmed': [('readonly', False)],
#                                'In Progress': [('readonly', False)]})
#     institution = fields.Many2one('sh.medical.health.center', string='Health Center', help="Health Center",
#                                   required=True, readonly=False,
#                                   states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
#     specialty_team = fields.One2many('sh.medical.specialty.team', 'name', string='Team Members',
#                                      help="Professionals Involved in the surgery", readonly=False,
#                                      states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
#     supplies = fields.One2many('sh.medical.specialty.supply', 'name', string='Supplies',
#                                help="List of the supplies required for the services", readonly=False,
#                                states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
#     department = fields.Many2one('sh.medical.health.center.ward', string='Department',
#                                  domain=lambda self: self.get_domain_department(),
#                                  help="Department of the selected Health Center", required=True, readonly=False,
#                                  states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
#     department_type = fields.Selection(WARD_TYPE, string='Loại khoa', related="department.type")
#     perform_room = fields.Many2one('sh.medical.health.center.ot', string='Performance room',
#                                    domain="[('department','=',department)]", readonly=False,
#                                    states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
#     state = fields.Selection(STATES, string='State', readonly=True, default=lambda *a: 'Draft')
#
#     other_bom = fields.Many2many('sh.medical.product.bundle', 'sh_specialty_bom_rel', 'specialty_id', 'bom_id',
#                                  string='All BOM of service',
#                                  domain="[('service_id', 'in', services),('region', '=', region),('type', '=', 'Specialty')]")
#
#     #  check công ty hiện tại của người dùng với công ty của phiếu
#     check_current_company = fields.Boolean(string='Cty hiện tại', compute='_check_current_company')
#
#     #  domain vật tư và thuốc theo kho của phòng
#     supply_domain = fields.Many2many('sh.medical.medicines', string='Supply domain', compute='_get_supply_domain')
#
#     uom_price = fields.Integer(string='Số lượng thực hiện',
#                                help="Răng/cm2/...", default=1, compute="_get_uom_price()", store=True)
#
#     show_specialty = fields.Boolean(string='Check chuyên khoa?', compute='_check_specialty')
#
#     # trường ghi nhận phiếu được chỉ định thêm ngoài cấu hình
#     is_new_request = fields.Boolean(string='Là chỉ định thêm', help="Phiếu được chỉ định thêm", default=False)
#
#     # vùng miền
#     region = fields.Selection(REGION, string='Miền', help="Vùng miền", related="institution.region")
#
#     @api.depends('teeths')
#     def _get_uom_price(self):
#         for record in self.with_env(self.env(su=True)):
#             if record.teeths:
#                 record.uom_price = len(record.teeths)
#             else:
#                 record.uom_price = 1
#
#     @api.depends('department')
#     def _check_specialty(self):
#         for record in self.with_env(self.env(su=True)):
#             record.show_specialty = False
#
#             # check quyền để hiện nút xem chi tiết phiếu
#             if self.env.user.has_group(
#                     'shealth_all_in_one.group_sh_medical_physician_spa') and record.department.type == 'Spa':
#                 record.show_specialty = True
#             elif self.env.user.has_group(
#                     'shealth_all_in_one.group_sh_medical_physician_laser') and record.department.type == 'Laser':
#                 record.show_specialty = True
#             elif self.env.user.has_group(
#                     'shealth_all_in_one.group_sh_medical_physician_odontology') and record.department.type == 'Odontology':
#                 record.show_specialty = True
#
#     @api.onchange('uom_price')
#     def onchange_uom_price(self):
#         if self.department and self.department.type == 'Odontology':
#             if self.uom_price < 0:
#                 raise ValidationError(_('Số lượng phải > 0'))
#
#             if self.uom_price > self.walkin.uom_price:
#                 raise ValidationError(_('Số lượng phải ít hơn số lượng từ Phiếu khám.'))
#
#             self.supplies = False
#
#     # cộng dồn số lượng vật tư nếu đã nhập rồi
#     @api.onchange('supplies')
#     def _onchange_supplies(self):
#         if self.supplies:
#             id_supplies = {}
#             inx = 0
#             for supply in self.supplies:
#                 if str(supply.supply.id) in id_supplies:
#                     # print('đã có: cộng dồn số lượng')
#                     qty_sup = self.supplies[id_supplies[str(supply.supply.id)]].qty_used + supply.qty_used
#                     self.supplies[id_supplies[str(supply.supply.id)]].qty_used = qty_sup
#                     self.supplies = [(2, supply.id, False)]
#                 else:
#                     id_supplies[str(supply.supply.id)] = inx
#                     # print('chưa có')
#                 inx += 1
#
#     @api.depends('institution.his_company')
#     def _check_current_company(self):
#         for record in self:
#             record.check_current_company = True if record.institution.his_company == self.env.company else False
#
#     @api.depends('perform_room')
#     def _get_supply_domain(self):
#         for record in self:
#             record.supply_domain = False
#             room = record.perform_room
#             if room:
#                 locations = room.location_medicine_stock + room.location_supply_stock
#                 if locations:
#                     products = self.env['stock.quant'].search(
#                         [('quantity', '>', 0), ('location_id', 'in', locations.ids)]).filtered(
#                         lambda q: q.reserved_quantity < q.quantity).mapped('product_id')
#                     if products:
#                         medicines = self.env['sh.medical.medicines'].search([('product_id', 'in', products.ids)])
#                         record.supply_domain = [(6, 0, medicines.ids)]
#
#     @api.onchange('date_requested', 'services_date', 'services_end_date')
#     def _onchange_date_specialty(self):
#         if self.services_date and self.date_requested and self.services_end_date:
#             if self.services_date < self.date_requested or self.services_date > self.services_end_date:
#                 raise UserError(
#                     _(
#                         'Thông tin không hợp lệ! Ngày giờ thực hiện phải sau ngày giờ chỉ định và trước ngày kết thúc!'))
#
#     def write(self, vals):
#         res = super(SHealthSpecialty, self).write(vals)
#
#         for record in self.with_env(self.env(su=True)):
#             # CASE ĐỔI CHI NHÁNH THỰC HIỆN: Cập nhật lại công ty ở SO để ghi nhận doanh thu cho cơ sở thự hiện
#             if vals.get('institution'):
#                 institution_detail = self.env['sh.medical.health.center'].browse(vals.get('institution'))
#
#                 # lấy kho của công ty
#                 ins_warehouse = self.env['stock.warehouse'].with_env(self.env(su=True)).search(
#                     [('company_id', '=', institution_detail.his_company.id)], limit=1)
#                 if not ins_warehouse:
#                     raise ValidationError(_('Công ty bạn chọn không có kho hàng!'))
#                 # print(record.walkin.sale_order_id.warehouse_id)
#                 # print(record.walkin.sale_order_id.company_id)
#                 # print(ins_warehouse.name)
#                 # print(institution_detail.his_company.name)
#
#                 record.walkin.sale_order_id.write(
#                     {'company_id': institution_detail.his_company.id, 'warehouse_id': ins_warehouse.id})
#                 # record.walkin.sale_order_id.company_id = institution_detail.his_company.id
#                 # record.walkin.sale_order_id.warehouse_id = ins_warehouse.id
#
#                 # print(institution_detail.his_company.id)
#
#             if vals.get('date_requested') or vals.get('services_date') or vals.get('services_end_date'):
#                 date_requested = vals.get('date_requested') or record.date_requested
#                 services_date = vals.get('services_date') or record.services_date
#                 services_end_date = vals.get('services_end_date') or record.services_end_date
#
#                 # format to date
#                 if isinstance(date_requested, str):
#                     date_requested = datetime.datetime.strptime(date_requested, '%Y-%m-%d %H:%M:%S')
#                 if isinstance(services_date, str):
#                     services_date = datetime.datetime.strptime(services_date, '%Y-%m-%d %H:%M:%S')
#                 if isinstance(services_end_date, str):
#                     services_end_date = datetime.datetime.strptime(services_end_date, '%Y-%m-%d %H:%M:%S')
#
#                 if services_date and date_requested and services_end_date and (
#                         services_date < date_requested or services_date > services_end_date):
#                     raise UserError(
#                         _(
#                             'Thông tin không hợp lệ! Ngày giờ thực hiện phải sau ngày giờ chỉ định và trước ngày kết thúc!'))
#
#             if vals.get('services'):
#                 # check dịch vụ đổi trong phiếu chuyên khoa: nếu xóa sẽ xóa dv sẽ xóa ở dv ở thành viên tham gia
#                 # thành viên tham gia
#                 for specialty_mem in record.specialty_team.mapped('service_performances').ids:
#                     if specialty_mem not in record.services.ids:
#                         record.specialty_team.write({'service_performances': [(3, specialty_mem)]})
#
#                 # vtth
#                 for specialty_sur in record.supplies.mapped('services').ids:
#                     if specialty_sur not in record.services.ids:
#                         record.supplies.write({'services': [(3, specialty_sur)]})
#
#         return res
#
#     def view_detail_specialty(self):
#         return {
#             'name': _('Chi tiết Chuyên khoa'),  # label
#             'type': 'ir.actions.act_window',
#             'view_mode': 'form',
#             'view_id': self.env.ref('shealth_all_in_one.sh_medical_specialty_view').id,
#             'res_model': 'sh.medical.specialty',  # model want to display
#             'target': 'current',  # if you want popup,
#             'context': {'form_view_initial_mode': 'edit'},
#             'res_id': self.id
#         }
#
#     @api.onchange('perform_room', 'other_bom')
#     def _onchange_other_bom(self):
#         self.supplies = False
#         if self.other_bom:
#             vals = []
#             check_duplicate = []
#             for record in self.other_bom:
#                 for record_line in record.products.filtered(lambda p: p.note == 'Specialty'):
#                     location = self.perform_room.location_supply_stock
#                     if record_line.product_id.medicament_type == 'Medicine':
#                         location = self.perform_room.location_medicine_stock
#                     # product = record_line.product_id.product_id  # product.product
#                     if location:
#                         # available_qty = self.env['stock.quant']._get_available_quantity(product_id=product, location_id=location)
#                         # if record_line.uom_id != product.uom_id:
#                         #     available_qty = product.uom_id._compute_quantity(available_qty, record_line.uom_id)
#
#                         uom_price = self.uom_price if self.department and self.department.type == 'Odontology' else 1
#
#                         # qty = min(record_line.quantity * uom_price, available_qty)
#                         qty = record_line.quantity * uom_price
#                         # if qty > 0:
#                         mats_id = record_line.product_id.id
#                         if mats_id not in check_duplicate:
#                             check_duplicate.append(mats_id)
#                             vals.append((0, 0, {'supply': mats_id,
#                                                 'qty': qty,
#                                                 'qty_used': qty,
#                                                 'uom_id': record_line.uom_id.id,
#                                                 'location_id': location.id,
#                                                 'services': [(4, record.service_id.id)],
#                                                 'notes': ''}))
#                         else:
#                             old_supply_index = check_duplicate.index(mats_id)
#                             vals[old_supply_index][2]['services'].append((4, record.service_id.id))
#                             vals[old_supply_index][2]['qty'] += qty
#                             vals[old_supply_index][2]['qty_used'] += qty
#
#             self.supplies = vals
#             # Đây là phần tính trung bình số lượng sử dụng theo số dịch vụ
#             for supply in self.supplies:
#                 if supply.uom_id.int_rounding:
#                     supply.qty_used = round(supply.qty_used / len(supply.services))
#                 else:
#                     supply.qty_used = supply.qty_used / len(supply.services)
#
#         # Tự động chọn BOM theo dịch vụ (Phiếu PTTT)
#         @api.onchange('services')
#         def get_default_other_bom(self):
#             self.other_bom = False
#             if self.services:
#                 list_result = []
#                 for service in self.services:
#                     other_bom = self.env['sh.medical.product.bundle'].search(
#                         [('service_id', '=', service._origin.id), ('type', '=', 'Surgery'),
#                          ('region', '=', self.region)],
#                         limit=1)
#                     if other_bom:
#                         list_result.append(other_bom.id)
#                 self.other_bom = [(6, 0, list_result)]
#
#     @api.onchange('institution')
#     def _onchange_institution(self):
#         # set khoa mac dinh la chuyen khoa cua co so y te
#         if self.institution:
#             specialty_dep = self.env['sh.medical.health.center.ward'].search(
#                 [('institution', '=', self.institution.id), ('type', '=', 'Specialty')], limit=1)
#             self.department = specialty_dep
#             self.perform_room = False
#
#     @api.onchange('department')
#     def _onchange_department(self):
#         if self.department:
#             self.perform_room = False
#
#     @api.model
#     def create(self, vals):
#         specialty_dep = self.env['sh.medical.health.center.ward'].search(
#             [('id', '=', vals['department'])])
#         # print(specialty_dep.type)
#         sequence = self.env['ir.sequence'].next_by_code(
#             'sh.medical.specialty.%s.%s' % (specialty_dep.type, vals['institution']))
#         if not sequence:
#             raise ValidationError(_('Định danh phiếu Chuyên khoa của Cơ sở y tế này đang không tồn tại!'))
#         vals['name'] = sequence
#         # print(sequence)
#         return super(SHealthSpecialty, self).create(vals)
#
#     def action_specialty_confirm(self):
#         if self.sudo().walkin.state == 'WaitPayment':
#             raise ValidationError(
#                 _('Bạn không thể xác nhận phiếu do Phiếu Khám liên quan của phiếu này chưa thu đủ tiền làm dịch vụ!'))
#
#         # Tự động chọn BOM theo dịch vụ
#         if self.services:
#             list_result = []
#             for service in self.services:
#                 other_bom = self.env['sh.medical.product.bundle'].search(
#                     [('service_id', '=', service._origin.id), ('type', '=', 'Specialty'),
#                      ('region', '=', self.region)],
#                     limit=1)
#                 if other_bom:
#                     list_result.append(other_bom.id)
#             self.other_bom = [(6, 0, list_result)]
#             self._onchange_other_bom()
#
#         # nếu chưa nhập vtth thì đổ bom theo cấu hình
#         if not self.supplies:
#             # add vat tu tieu hao ban dau cho chuyen khoa
#             sg_data = []
#             check_duplicate = []
#             # self.supplies = False #NÊN GIỮ LẠI VTTH ĐÃ NHẬP
#
#             for ser in self.services:
#                 # add vat tu tieu hao tong - ban dau
#                 for mats in ser.material_ids.filtered(lambda m: m.note == 'Specialty'):
#                     # print(mats)
#                     location = self.perform_room.location_supply_stock
#                     if mats.product_id.medicament_type == 'Medicine':
#                         location = self.perform_room.location_medicine_stock
#                     product = mats.product_id.product_id  # product.product
#                     if location:
#                         available_qty = self.env['stock.quant']._get_available_quantity(product_id=product,
#                                                                                         location_id=location)
#                         if mats.uom_id != product.uom_id:
#                             available_qty = product.uom_id._compute_quantity(available_qty, mats.uom_id)
#
#                         uom_price = self.uom_price if self.department and self.department.type == 'Odontology' else 1
#                         qty = min(mats.quantity * uom_price, available_qty)
#
#                         # if qty > 0:
#                         mats_id = mats.product_id.id
#                         if mats_id not in check_duplicate:
#                             check_duplicate.append(mats_id)
#                             sg_data.append((0, 0, {'supply': mats_id,
#                                                    'qty': mats.quantity * uom_price,
#                                                    'qty_used': qty,
#                                                    'uom_id': mats.uom_id.id,
#                                                    'location_id': location.id,
#                                                    'services': [(4, ser.id)],
#                                                    'notes': mats.note}))
#                         else:
#                             old_supply_index = check_duplicate.index(mats_id)
#                             sg_data[old_supply_index][2]['services'] += [(4, ser.id)],
#                             sg_data[old_supply_index][2]['qty'] += mats.quantity * uom_price
#                             sg_data[old_supply_index][2]['qty_used'] = min(
#                                 qty + sg_data[old_supply_index][2]['qty_used'], available_qty)
#
#             # ghi nhận ngày làm dịch vụ là ngày bấm xác nhận phiếu
#             self.write({'state': 'Confirmed', 'supplies': sg_data, 'services_date': fields.Datetime.now(),
#                         'services_end_date': fields.Datetime.now() + timedelta(hours=2)})
#         else:
#             self.write({'state': 'Confirmed'})
#
#     def reverse_materials(self):
#         num_of_location = len(self.supplies.mapped('location_id'))
#         pick_need_reverses = self.env['stock.picking'].search(
#             [('origin', 'ilike', 'THBN - %s - %s' % (self.name, self.walkin.name)),
#              ('company_id', '=', self.env.company.id)], order='create_date DESC', limit=num_of_location)
#         if pick_need_reverses:
#             for pick_need_reverse in pick_need_reverses:
#                 date_done = pick_need_reverse.date_done
#                 fail_pick_count = self.env['stock.picking'].search_count(
#                     [('name', 'ilike', pick_need_reverse.name), ('company_id', '=', self.env.company.id)])
#                 pick_need_reverse.name += '-FP%s' % fail_pick_count
#                 pick_need_reverse.move_ids_without_package.write(
#                     {'reference': pick_need_reverse.name})  # sửa cả trường tham chiếu của move.line (Dịch chuyển kho)
#
#                 new_wizard = self.env['stock.return.picking'].new(
#                     {'picking_id': pick_need_reverse.id})  # tạo new wizard chưa lưu vào db
#                 new_wizard._onchange_picking_id()  # chạy hàm onchange với tham số ở trên
#                 wizard_vals = new_wizard._convert_to_write(
#                     new_wizard._cache)  # lấy dữ liệu sau khi đã chạy qua onchange
#                 wizard = self.env['stock.return.picking'].with_context(reopen_flag=True, no_check_quant=True).create(
#                     wizard_vals)
#                 new_picking_id, pick_type_id = wizard._create_returns()
#                 new_picking = self.env['stock.picking'].browse(new_picking_id)
#                 new_picking.with_context(exact_location=True).action_assign()
#                 for move_line in new_picking.move_ids_without_package:
#                     for move_live_detail in move_line.move_line_ids:
#                         move_live_detail.qty_done = move_live_detail.product_uom_qty
#                     # move_line.quantity_done = move_line.product_uom_qty
#                 new_picking.with_context(force_period_date=date_done).button_validate()
#
#                 # sua ngay hoan thanh
#                 for move_line in new_picking.move_ids_without_package:
#                     move_line.move_line_ids.write(
#                         {'date': date_done})  # sửa ngày hoàn thành ở stock move line
#                 new_picking.move_ids_without_package.write(
#                     {'date': date_done})  # sửa ngày hoàn thành ở stock move
#
#                 new_picking.date_done = date_done
#                 new_picking.sci_date_done = date_done
#
#     def action_specialty_start(self):
#         if self.state == 'Done':
#             self.reverse_materials()
#             self.sudo().walkin.update_walkin_material(mats_types=['Specialty'])
#             res = self.write({'state': 'In Progress'})
#         else:
#             if self.services_date:
#                 services_date = self.services_date
#             else:
#                 services_date = datetime.datetime.now()
#             res = self.write({'state': 'In Progress', 'services_date': services_date})
#         # return res
#
#     # def action_specialty_cancel(self):
#     #     self.supplies = False
#     #     self.write({'state': 'Cancelled'})
#
#     def action_cancelled(self):
#         if self.state != 'Draft':
#             raise ValidationError('Bạn chỉ có thể hủy khi phiếu ở trạng thái NHÁP')
#         else:
#             self.state = 'Cancelled'
#
#     def action_specialty_set_to_draft(self):
#         self.other_bom = False
#         self.supplies = False
#         self.write({'state': 'Draft'})
#
#     # def action_specialty_set_to_confirm(self):
#     #     self.other_bom = False
#     #     self.supplies = False
#     #     self.write({'state': 'Confirmed'})
#
#     def action_specialty_end(self):
#         self.ensure_one()
#         if len(self.other_bom) != len(self.services):
#             raise ValidationError('Số lượng BOM phải bằng số lượng dịch vụ.')
#         if not self.supplies:
#             raise ValidationError('Bạn phải nhập VTTH cho phiếu trước khi xác nhận hoàn thành!')
#         if not self.specialty_team:
#             raise ValidationError('Bạn cần nhập Thành viên tham gia trước khi xác nhận hoàn thành')
#
#         # tru vat tu theo tieu hao của phiếu khám chuyên khoa
#         dept = self.department
#         if self.services_end_date:
#             services_end_date = self.services_end_date
#         else:
#             services_end_date = fields.Datetime.now()
#
#         # 20220320 - tungnt - onnet
#         default_production_location = self.env['stock.location'].get_default_production_location_per_company()
#
#         vals = {}
#         validate_str = ''
#
#         for mat in self.supplies:
#             if mat.qty_used > 0:  # CHECK SO LUONG SU DUNG > 0
#                 quantity_on_hand = self.env['stock.quant']._get_available_quantity(mat.supply.product_id,
#                                                                                    mat.location_id)  # check quantity trong location
#                 if mat.uom_id != mat.supply.uom_id:
#                     mat.write({'qty_used': mat.uom_id._compute_quantity(mat.qty_used, mat.supply.uom_id),
#                                'uom_id': mat.supply.uom_id.id})  # quy so suong su dung ve don vi chinh cua san pham
#
#                 if quantity_on_hand < mat.qty_used:
#                     validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
#                         mat.supply.default_code, mat.supply.name, str(quantity_on_hand), str(mat.uom_id.name),
#                         mat.location_id.name)
#
#                 else:  # truong one2many trong stock picking de tru cac product trong inventory
#                     sub_vals = {
#                         'name': 'THBN: ' + mat.supply.product_id.name,
#                         'origin': str(self.sudo().walkin.id) + "-" + str(self.services.ids),  # mã pk-mã dịch vụ
#                         'date': services_end_date,
#                         'company_id': self.env.company.id,
#                         'date_expected': services_end_date,
#                         # 'date_done': services_end_date,
#                         'product_id': mat.supply.product_id.id,
#                         'product_uom_qty': mat.qty_used,
#                         'product_uom': mat.uom_id.id,
#                         'location_id': mat.location_id.id,
#                         'location_dest_id': default_production_location.id,
#                         'partner_id': self.patient.partner_id.id,
#                         # xuat cho khach hang/benh nhan nao
#                         'material_line_object': mat._name,
#                         'material_line_object_id': mat.id,
#                     }
#                     if not vals.get(str(mat.location_id.id)):
#                         vals[str(mat.location_id.id)] = [sub_vals]
#                     else:
#                         vals[str(mat.location_id.id)].append(sub_vals)
#
#         # neu co vat tu tieu hao
#         if vals and validate_str == '':
#             # tao phieu xuat kho
#             picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
#                                                                   ('warehouse_id', '=',
#                                                                    self.institution.warehouse_ids[0].id)],
#                                                                  limit=1).id
#             # picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
#             #                                                       ('warehouse_id', '=',
#             #                                                        self.env.ref('stock.warehouse0').id)],
#             #                                                      limit=1).id
#             for location_key in vals:
#                 pick_note = 'THBN - %s - %s - %s' % (self.name, self.sudo().walkin.name, location_key)
#                 pick_vals = {'note': pick_note,
#                              'origin': pick_note,
#                              'partner_id': self.patient.partner_id.id,
#                              'patient_id': self.patient.id,
#                              'picking_type_id': picking_type,
#                              'location_id': int(location_key),
#                              'location_dest_id': default_production_location.id,
#                              'date_done': services_end_date,
#                              # xuat cho khach hang/benh nhan nao
#                              # 'immediate_transfer': True,  # sẽ gây lỗi khi dùng lô, pick với immediate_transfer sẽ ko cho tạo move, chỉ tạo move line
#                              # 'move_ids_without_package': vals[location_key]
#                              }
#                 fail_pick_name = self.env['stock.picking'].search(
#                     [('origin', 'ilike', 'THBN - %s - %s - %s' % (self.name, self.sudo().walkin.name, location_key))],
#                     limit=1).name
#                 if fail_pick_name:
#                     pick_vals['name'] = fail_pick_name.split('-', 1)[0]
#                 stock_picking = self.env['stock.picking'].create(pick_vals)
#                 for move_val in vals[location_key]:
#                     move_val['name'] = stock_picking.name + " - " + move_val['name']
#                     move_val['picking_id'] = stock_picking.id
#                     self.env['stock.move'].create(move_val)
#
#                 # TU DONG XÁC NHẬN XUAT KHO
#                 stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
#                 for move_line in stock_picking.move_ids_without_package:
#                     for move_live_detail in move_line.move_line_ids:
#                         move_live_detail.qty_done = move_live_detail.product_uom_qty
#                     # move_line.quantity_done = move_line.product_uom_qty
#                 stock_picking.with_context(
#                     force_period_date=services_end_date).sudo().button_validate()  # ham tru product trong inventory, sudo để đọc stock.valuation.layer
#
#                 # sua ngay hoan thanh
#                 for move_line in stock_picking.move_ids_without_package:
#                     move_line.move_line_ids.write({'date': services_end_date})  # sửa ngày hoàn thành ở stock move line
#                 stock_picking.move_ids_without_package.write(
#                     {'date': services_end_date})  # sửa ngày hoàn thành ở stock move
#                 stock_picking.date_done = services_end_date
#                 stock_picking.sci_date_done = services_end_date
#
#                 stock_picking.create_date = self.services_date
#
#                 # Cập nhật ngược lại picking_id vào mats để truyền số liệu sang vật tư phiếu khám
#                 self.supplies.filtered(lambda s: s.location_id.id == int(location_key)).write(
#                     {'picking_id': stock_picking.id})
#
#         elif validate_str != '':
#             raise ValidationError(
#                 _("Các loại Thuốc và Vật tư sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))
#
#         # tạo đơn thuốc mang về cho bệnh nhân theo BOM dịch vụ
#         # prescription_wakin = []
#         # prescription_line = []
#         # flag_pres = False
#         # for service_done in self.services:
#         #     if service_done.prescription_ids:
#         #         flag_pres = True
#         #         for prescription in service_done.prescription_ids:
#         #             prescription_line.append((0, 0, {
#         #                 'name': prescription.product_id.id,
#         #                 'qty': prescription.qty,
#         #                 'dose': prescription.dose,
#         #                 'dose_unit_related': prescription.dose_unit,
#         #                 'common_dosage': prescription.common_dosage.id,
#         #                 'duration': prescription.duration,
#         #                 'duration_period': prescription.duration_period,
#         #                 'info': service_done.name}))
#         #
#         # if flag_pres:
#         #     if len(self.walkin.prescription_ids)>0:
#         #         prescription_wakin = self.walkin.prescription_ids[0]
#         #         prescription_wakin.prescription_line = prescription_line
#         #     else:
#         #         #lấy thông tin tủ kê đơn của bệnh viện
#         #         print(self.institution.location_medicine_stock.id)
#         #         prescription_wakin.append((0, 0, {
#         #             'patient': self.patient.id,
#         #             'date': services_end_date,
#         #             'doctor': self.physician.id,
#         #             'location_id': self.institution.location_medicine_stock.id,
#         #             'walkin': self.walkin.id,
#         #             'prescription_line': prescription_line,
#         #             'state': 'Draft'}))
#         #
#         # self.walkin.write({'prescription_ids': prescription_wakin})
#
#         # log access patient
#         # data_log = self.env['sh.medical.patient.log'].search([('walkin', '=', self.walkin.id)])
#         # data_ck = False
#         # for data in data_log:
#         #     # nếu đã có data log cho ck khoa này rồi
#         #     if data.department.id == self.department.id:
#         #         data_ck = data
#         #     # nếu có log khoa KB rồi thì cập nhật ngày ra cho khoa kb là ngày bắt đầu làm dịch vụ
#         #     if data.department.type == 'Examination':
#         #         data.date_out = self.services_date
#         # # nếu chưa có data log=> tạo log
#         # if not data_ck:
#         #     vals_log = {'walkin': self.walkin.id,
#         #                 'patient': self.patient.id,
#         #                 'department': self.department.id,
#         #                 'date_in': self.services_date}
#         #     self.env['sh.medical.patient.log'].create(vals_log)
#         # else:
#         #     data_ck.date_in = self.services_date
#         #     data_ck.date_out = self.services_end_date
#
#         res = self.write({'state': 'Done', 'services_end_date': services_end_date})
#
#         # cap nhat vat tu cho phieu kham
#         self.sudo().walkin.update_walkin_material(mats_types=['Specialty'])
#         # return res
#
#     def unlink(self):
#         for specialty in self.filtered(lambda sp: sp.state not in ['Draft']):
#             # raise UserError(_('You can not delete a record that is not in Draft !!'))
#             raise UserError(_('Bạn không thể xóa Phiếu Chuyên khoa khi phiếu đang không ở trạng thái Nháp!'))
#         return super(SHealthSpecialty, self).unlink()
#
#     def reset_all_supply(self):
#         for specialty in self.filtered(lambda sp: sp.state not in ['Draft', 'Done']):
#             specialty.supplies = False
#

# Inheriting Ward module to add "Imaging" screen reference
class SHealthWard(models.Model):
    _inherit = 'sh.medical.health.center.ward'

    surgeries = fields.One2many('sh.medical.surgery', 'department', string='Surgeries')
    count_surgery_not_done = fields.Integer('Surgeries not completed', compute="_count_surgery_not_done")

    specialtys = fields.One2many('sh.medical.specialty', 'department', string='Specialtys')
    count_specialty_not_done = fields.Integer('Specialtys not completed', compute="_count_specialty_not_done")

    def _count_surgery_not_done(self):
        oe_surgs = self.env['sh.medical.surgery']
        for ls in self:
            domain = [('state', '!=', 'Done'), ('department', '=', ls.id)]
            ls.count_surgery_not_done = oe_surgs.search_count(domain)
        return True

    def _count_specialty_not_done(self):
        oe_specs = self.env['sh.medical.specialty']
        for ls in self:
            domain = [('state', '!=', 'Done'), ('department', '=', ls.id)]
            ls.count_specialty_not_done = oe_specs.search_count(domain)
        return True


class wizardMultiSupply(models.TransientModel):
    _name = 'wizard.multi.supply'
    _description = 'Chọn nhiều vật tư'

    def get_domain_supply(self):
        if self.env.context.get('medicament_type'):
            return [('medicament_type', '=', self.env.context.get('medicament_type'))]
        else:
            return []

    supply_ids = fields.Many2many('sh.medical.medicines', string="Thuốc/VTTH",
                                  domain=lambda self: self.get_domain_supply())
    model_binding = fields.Char('Đối tượng')
    notes = fields.Char(string='Loại')
    room_use = fields.Many2one('sh.medical.health.center.ot', string='Phòng sử dụng')

    def apply_data(self):
        if self.model_binding != '' and self.supply_ids:
            for line in self.supply_ids:
                if line.medicament_type == 'Medicine':
                    location_id = self.room_use.location_medicine_stock.id
                else:
                    location_id = self.room_use.location_supply_stock.id

                res = self.env[self.model_binding].create({
                    'medicament_type': line.medicament_type,
                    'supply': line.id,
                    'qty_used': 1,
                    'name': self._context.get('active_id'),
                    'uom_id': line.uom_id.id,
                    'location_id': location_id,
                    'notes': self.notes
                })
        return
