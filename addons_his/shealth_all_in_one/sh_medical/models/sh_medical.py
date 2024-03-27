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

import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
import time
from lxml import etree
import json
import datetime
from datetime import timedelta
from odoo.osv import expression
from odoo.tools import pycompat

_logger = logging.getLogger(__name__)


# Foreign Management
class SHealthForeign(models.Model):
    _name = 'sh.foreign'
    _description = 'Thông tin ngoại kiều'

    name = fields.Char(size=256, string='Tên', required=True, help='Tên ngoại kiều')


# Family Management
class SHealthFamily(models.Model):
    _name = 'sh.medical.patient.family'
    _description = 'Information about family of patient'

    # FAMILY_RELATION = [
    #             ('Father', 'Father'),
    #             ('Mother', 'Mother')
    # ]

    name = fields.Char(size=256, string='Name', required=True, help='Family Member Name')
    phone = fields.Char(string='Phone', help='Family Member Phone')
    # relation = fields.Selection(FAMILY_RELATION, string='Relation', help="Family Relation", index=True)
    type_relation = fields.Many2one('type.relative', string='Relation', help="Family Relation", index=True)
    age = fields.Selection([(str(num), str(num)) for num in
                            reversed(range((datetime.datetime.now().year) - 80, datetime.datetime.now().year))],
                           'Năm sinh')
    address = fields.Text(string='Địa chỉ liên hệ', help='Địa chỉ liên hệ')
    deceased = fields.Boolean(string='Deceased?', help="Mark if the family member has died")
    patient_id = fields.Many2one('sh.medical.patient', 'Patient', required=True, ondelete='cascade', index=True)


# Patient Management

class SHealthPatient(models.Model):
    _name = 'sh.medical.patient'
    _description = 'Information of patient'
    _inherits = {
        'res.partner': 'partner_id',
    }

    _order = "code_customer desc"

    MARITAL_STATUS = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Widowed', 'Widowed'),
        ('Divorced', 'Divorced'),
        ('Separated', 'Separated'),
    ]

    # SEX = [
    #     ('Male', 'Male'),
    #     ('Female', 'Female'),
    # ]

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

    def _app_count(self):
        oe_apps = self.env['sh.medical.appointment']
        for pa in self:
            domain = [('patient', '=', pa.id)]
            app_ids = oe_apps.search(domain)
            apps = oe_apps.browse(app_ids)
            app_count = 0
            for ap in apps:
                app_count += 1
            pa.app_count = app_count
        return True

    def _prescription_count(self):
        oe_pres = self.env['sh.medical.prescription']
        for pa in self:
            domain = [('patient', '=', pa.id)]
            pres_ids = oe_pres.search(domain)
            pres = oe_pres.browse(pres_ids)
            pres_count = 0
            for pr in pres:
                pres_count += 1
            pa.prescription_count = pres_count
        return True

    def _admission_count(self):
        oe_admission = self.env['sh.medical.inpatient']
        for adm in self:
            domain = [('patient', '=', adm.id)]
            admission_ids = oe_admission.search(domain)
            admissions = oe_admission.browse(admission_ids)
            admission_count = 0
            for ad in admissions:
                admission_count += 1
            adm.admission_count = admission_count
        return True

    def _vaccine_count(self):
        oe_vac = self.env['sh.medical.vaccines']
        for va in self:
            domain = [('patient', '=', va.id)]
            vec_ids = oe_vac.search(domain)
            vecs = oe_vac.browse(vec_ids)
            vecs_count = 0
            for vac in vecs:
                vecs_count += 1
            va.vaccine_count = vecs_count
        return True

    def _invoice_count(self):
        oe_invoice = self.env['account.move']
        for inv in self:
            invoice_ids = self.env['account.move'].search([('patient', '=', inv.id)])
            invoices = oe_invoice.browse(invoice_ids)
            invoice_count = 0
            for inv_id in invoices:
                invoice_count += 1
            inv.invoice_count = invoice_count
        return True

    def _patient_age(self):
        def compute_age_from_dates(patient_dob, patient_deceased, patient_dod, patient_yod):
            now = datetime.datetime.now()
            if (patient_dob):
                dob = datetime.datetime.strptime(patient_dob.strftime('%Y-%m-%d'), '%Y-%m-%d')
                if patient_deceased:
                    dod = datetime.datetime.strptime(patient_dod.strftime('%Y-%m-%d'), '%Y-%m-%d')
                    delta = dod - dob
                    deceased = " (deceased)"
                    # years_months_days = _(str(delta.days // 365) + " years " + str(delta.days % 365) + " days" + deceased)
                    # years_months_days = _("%s tuổi %s ngày %s"%(str(delta.days // 365),str(delta.days%365),deceased))
                    years_months_days = _("%s tuổi " % (str(delta.days // 365)))
                else:
                    delta = now - dob
                    # years_months_days = _(str(delta.days // 365) + " years " + str(delta.days % 365) + " days")
                    # years_months_days = _("%s tuổi %s ngày"%(str(delta.days // 365),str(delta.days%365)))
                    years_months_days = _("%s tuổi" % (str(delta.days // 365)))
            elif patient_yod:
                years_months_days = datetime.datetime.now().year - int(patient_yod)
            else:
                years_months_days = _("No DoB !")

            return years_months_days

        for patient_data in self:
            patient_data.age = compute_age_from_dates(patient_data.birth_date, patient_data.deceased,
                                                      patient_data.birth_date, patient_data.year_of_birth)
        return True

    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True, ondelete='cascade',
                                 help='Partner-related data of the patient')
    family = fields.One2many('sh.medical.patient.family', 'patient_id', string='Family')
    ssn = fields.Char(size=256, string='SSN')
    current_insurance = fields.Many2one('sh.medical.insurance', string="Insurance",
                                        domain="[('patient','=', active_id),('state','=','Active')]",
                                        help="Insurance information. You may choose from the different insurances belonging to the patient")
    doctor = fields.Many2one('sh.medical.physician', string='Family Physician',
                             help="Current primary care physician / family doctor",
                             domain=[('is_pharmacist', '=', False)])
    # dob = fields.Date(string='Date of Birth')
    age = fields.Char(compute=_patient_age, size=32, string='Patient Age',
                      help="It shows the age of the patient in years(y), months(m) and days(d).\nIf the patient has died, the age shown is the age at time of death, the age corresponding to the date on the death certificate. It will show also \"deceased\" on the field")
    # age = fields.Char(string='Patient Age', help="It shows the age of the patient in years(y), months(m) and days(d).\nIf the patient has died, the age shown is the age at time of death, the age corresponding to the date on the death certificate. It will show also \"deceased\" on the field")
    # sex = fields.Selection(SEX, string='Sex', index=True)
    marital_status = fields.Selection(MARITAL_STATUS, string='Marital Status')
    blood_type = fields.Selection(BLOOD_TYPE, string='Blood Type')
    rh = fields.Selection(RH, string='Rh')
    # identification_code = fields.Char(string='Patient ID', size=256, help='Patient Identifier provided by the Health Center', copy=False)
    ethnic_group = fields.Many2one('sh.medical.ethnicity', 'Dân tộc',
                                   default=lambda self: self.env.ref('shealth_all_in_one.sheth_kinh').id)
    foreign = fields.Many2one('sh.foreign', 'Ngoại kiều')
    critical_info = fields.Text(string='Important disease, allergy or procedures information',
                                help="Write any important information on the patient's disease, surgeries, allergies, ...")
    general_info = fields.Text(string='General Information', help="General information about the patient")
    genetic_risks = fields.Many2many('sh.medical.genetics', 'sh_genetic_risks_patient_rel', 'patient_id',
                                     'genetic_risk_id', string='Genetic Risks')
    deceased = fields.Boolean(string='Patient Deceased ?', help="Mark if the patient has died")
    dod = fields.Date(string='Date of Death')
    cod = fields.Many2one('sh.medical.pathology', string='Cause of Death')
    app_count = fields.Integer(compute=_app_count, string="Appointments")
    prescription_count = fields.Integer(compute=_prescription_count, string="SL Đơn thuốc")
    admission_count = fields.Integer(compute=_admission_count, string="Admission / Discharge")
    vaccine_count = fields.Integer(compute=_vaccine_count, string="Vaccines")
    invoice_count = fields.Integer(compute=_invoice_count, string="SL Hóa đơn")
    # invoice_count = fields.Integer(string="Invoices")
    sh_patient_user_id = fields.Many2one('res.users', string='Responsible Odoo User')
    prescription_line = fields.One2many('sh.medical.prescription.line', 'patient', string='Medicines', readonly=True)
    prescription_ids = fields.One2many('sh.medical.prescription', 'patient', string='Các Đơn thuốc', readonly=True)

    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',
                                 default=lambda self: self.env.ref('base.vn').id)

    pass_port = fields.Char('CMND/Hộ chiếu')
    function = fields.Char(string='Nghề nghiệp', default='Tự do')

    # Phiếu tái khám
    evaluation_ids = fields.One2many('sh.medical.evaluation', 'patient', string='Evaluation')

    _sql_constraints = [
        ('code_sh_patient_userid_uniq', 'unique (sh_patient_user_id)',
         "Selected 'Responsible' user is already assigned to another patient !")
    ]

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(SHealthPatient, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone', 'mobile', 'phone_sanitized']:
                fields[field_name]['exportable'] = False

        return fields

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
            default['name'] = self.name + " (Copy)"

        return super(SHealthPatient, self).copy(default=default)

    @api.model
    def create(self, vals):
        vals['is_patient'] = True
        health_patient = super(SHealthPatient, self).create(vals)
        # TỰ ĐỘNG CẬP NHẬT MÃ TỰ TĂNG NẾU KO CÓ
        # if not health_patient.identification_code:
        #     sequence = self.env['ir.sequence'].next_by_code('sh.medical.patient')
        #     health_patient.identification_code = sequence

        return health_patient

    #
    # @api.constrains('dob')
    # def _check_dob(self):
    #     for record in self:
    #         if record.dob > fields.Date.today():
    #             raise ValidationError(_(
    #                 "Ngày sinh không thể lớn hơn ngày hiện tại!"))

    # @api.onchange('dob')
    # def onchange_dob(self):
    #     if self.dob and self.dob > fields.Date.today():
    #         self.dob = False
    #         raise ValidationError(_(
    #                 "Ngày sinh không thể lớn hơn ngày hiện tại!"))

    # @api.onchange('state_id')
    # def onchange_state(self):
    #     if self.state_id:
    #         self.country_id = self.state_id.country_id.id

    @api.onchange('foreign')
    def onchange_state(self):
        if self.foreign:
            self.ethnic_group = False

    def print_patient_label(self):
        return self.env.ref('shealth_all_in_one.action_report_patient_label').report_action(self)

    def name_get(self):
        res = []
        for category in self:
            if category.year_of_birth:
                res.append((category.id,
                            '[%s] %s - %s' % (category.code_customer, category.name[0:50], category.year_of_birth)))
            else:
                res.append((category.id, '[%s] %s' % (category.code_customer, category.name[0:50])))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name), ('code_customer', operator, name), ('phone', operator, name)]
        patient = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(patient).name_get()


# Physician Management

class SHealthPhysicianSpeciality(models.Model):
    _name = "sh.medical.speciality"
    _description = "Physician Speciality"

    name = fields.Char(string='Description', size=128, help="ie, Addiction Psychiatry", translate=True, required=True)
    code = fields.Char(string='Code', size=128, help="ie, ADP")

    _order = 'name'
    _sql_constraints = [
        ('code_uniq', 'unique (name)', 'The Medical Speciality code must be unique')]


class SHealthTeamRole(models.Model):
    _name = "sh.medical.team.role"
    _description = "Vai trò trong nhóm thực hiện dịch vụ"

    ROLE_TYPE = [
        ('spa', 'Spa'),
        ('laser', 'Laser'),
        ('surgery', 'Phẫu thuật'),
        ('odontology', 'Nha khoa')
    ]

    name = fields.Char(string='Description', size=128, translate=True, required=True)
    type = fields.Selection(ROLE_TYPE, string='Loại')

    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Tên vai trò phải là duy nhất!')]


class SHealthPhysicianDegree(models.Model):
    _name = "sh.medical.degrees"
    _description = "Physicians Degrees"

    name = fields.Char(string='Degree', size=128, required=True)
    keyword = fields.Char(string='Keyword', size=128)
    full_name = fields.Char(string='Full Name', translate=True, size=128)
    education_level = fields.Selection(
        [('saudaihoc', 'Sau đại học'), ('daihoc', 'Đại học'), ('trungcap', 'Trung Cấp'), ('socap', 'Sơ Cấp')],
        string='Cấp học', translate=True, default='trungcap')
    physician_ids = fields.Many2many('sh.medical.physician', id1='degree_id', id2='physician_id', string='Physicians')

    _sql_constraints = [
        ('full_name_uniq', 'unique (name,education_level)', 'The Medical Degree must be unique')]


class SHealthPhysician(models.Model):
    _name = "sh.medical.physician"
    _description = "Information about the doctor"
    _inherits = {
        'hr.employee': 'employee_id',
    }

    CONSULTATION_TYPE = [
        ('Residential', 'Residential'),
        ('Visiting', 'Visiting'),
        ('Other', 'Other'),
    ]

    APPOINTMENT_TYPE = [
        ('Not on Weekly Schedule', 'Not on Weekly Schedule'),
        ('On Weekly Schedule', 'On Weekly Schedule'),
    ]

    def _app_count(self):
        oe_apps = self.env['sh.medical.appointment']
        for pa in self:
            domain = [('doctor', '=', pa.id)]
            app_ids = oe_apps.search(domain)
            apps = oe_apps.browse(app_ids)
            app_count = 0
            for ap in apps:
                app_count += 1
            pa.app_count = app_count
        return True

    def _prescription_count(self):
        oe_pres = self.env['sh.medical.prescription']
        for pa in self:
            domain = [('doctor', '=', pa.id)]
            pres_ids = oe_pres.search(domain)
            pres = oe_pres.browse(pres_ids)
            pres_count = 0
            for pr in pres:
                pres_count += 1
            pa.prescription_count = pres_count
        return True

    employee_id = fields.Many2one('hr.employee', string='Related Employee', required=True, ondelete='cascade',
                                  help='Employee-related data of the physician')
    # institution = fields.Many2one('sh.medical.health.center', string='Institution', help="Institution where doctor works")
    institution = fields.Many2many('sh.medical.health.center', 'sh_medical_physician_institution_rel', 'physician_id',
                                   'ins_id', string='Institution', help="Institution where doctor works")
    department = fields.Many2many('sh.medical.health.center.ward', 'sh_medical_physician_department_rel',
                                  'physician_id', 'dep_id', string='Khoa/Phòng',
                                  domain="[('institution', '=', institution)]", help="Department where doctor works")
    code = fields.Char(string='Licence ID', size=128, help="Physician's License ID")
    speciality = fields.Many2one('sh.medical.speciality', string='Speciality', help="Speciality Code")
    consultancy_type = fields.Selection(CONSULTATION_TYPE, string='Consultancy Type',
                                        help="Type of Doctor's Consultancy", default=lambda *a: 'Residential')
    consultancy_price = fields.Integer(string='Consultancy Charge', help="Physician's Consultancy price")
    available_lines = fields.One2many('sh.medical.physician.line', 'physician_id', string='Physician Availability')
    degree_id = fields.Many2many('sh.medical.degrees', id1='physician_id', id2='degree_id', string='Degrees')
    app_count = fields.Integer(compute=_app_count, string="Appointments")
    prescription_count = fields.Integer(compute=_prescription_count, string="Prescriptions")
    is_pharmacist = fields.Boolean(string='Pharmacist?', default=lambda *a: False)
    sh_user_id = fields.Many2one('res.users', string='Responsible Odoo User')
    appointment_type = fields.Selection(APPOINTMENT_TYPE, string='Allow Appointment on?',
                                        default=lambda *a: 'Not on Weekly Schedule')
    tradenames = fields.Char('Tên thương mại')
    is_doctor_order = fields.Boolean('Bác sĩ order')

    _sql_constraints = [
        ('code_sh_physician_userid_uniq', 'unique(sh_user_id)',
         "Selected 'Responsible' user is already assigned to another physician !")
    ]

    def name_get(self):
        res = []
        for physician in self:
            res.append((physician.id, _('[%s] - %s - %s - %s') % (
                physician.tradenames, physician.name,
                physician.employee_id.birthday.year, physician.speciality.name)))
        return res

    # @api.onchange('state_id')
    # def onchange_state(self):
    #     if self.state_id:
    #         self.country_id = self.state_id.country_id.id

    @api.onchange('address_id')
    def _onchange_address(self):
        self.work_phone = self.address_id.phone
        self.mobile_phone = self.address_id.mobile

    @api.onchange('name')
    def _onchange_name(self):
        self.tradenames = self.name

    @api.onchange('company_id')
    def _onchange_company(self):
        address = self.company_id.partner_id.address_get(['default'])
        self.address_id = address['default'] if address else False

    @api.onchange('user_id')
    def _onchange_user(self):
        self.work_email = self.user_id.email
        self.name = self.user_id.name
        self.image = self.user_id.image

    def write(self, vals):
        if 'name' in vals:
            vals['name_related'] = vals['name']
        return super(SHealthPhysician, self).write(vals)


#
class ResUsers(models.Model):
    _inherit = "res.users"

    physician_ids = fields.One2many('sh.medical.physician', 'sh_user_id', string='Physicians', auto_join=True)


class SHealthCentersWards(models.Model):
    _inherit = "sh.medical.health.center.ward"

    physician = fields.Many2many('sh.medical.physician', 'sh_medical_physician_department_rel',
                                 'dep_id', 'physician_id', string='Physicians', help="Physicians in Department")


class SHealthPhysicianLine(models.Model):
    # Array containing different days name
    PHY_DAY = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    _name = "sh.medical.physician.line"
    _description = "Information about doctor availability"

    name = fields.Selection(PHY_DAY, string='Available Day(s)', required=True)
    start_time = fields.Float(string='Start Time (24h format)')
    end_time = fields.Float(string='End Time (24h format)')
    physician_id = fields.Many2one('sh.medical.physician', string='Physician', index=True, ondelete='cascade')


# Appointment Management

class SHealthAppointment(models.Model):
    _name = 'sh.medical.appointment'
    _description = 'Appointment'
    _inherit = ['mail.thread']
    _order = "appointment_date desc"

    URGENCY_LEVEL = [
        ('Normal', 'Normal'),
        ('Urgent', 'Urgent'),
        ('Medical Emergency', 'Medical Emergency'),
    ]

    PATIENT_STATUS = [
        ('Ambulatory', 'Ambulatory'),
        ('Outpatient', 'Outpatient'),
        ('Inpatient', 'Inpatient'),
    ]

    APPOINTMENT_STATUS = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Invoiced', 'Invoiced'),
    ]

    # Automatically detect logged in physician

    def _get_physician(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain, limit=1)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    # Calculating Appointment End date

    def _get_appointment_end(self):
        for apm in self:
            end_date = False
            duration = 1
            if apm.duration:
                duration = apm.duration
            if apm.appointment_date:
                end_date = datetime.datetime.strptime(apm.appointment_date.strftime("%Y-%m-%d %H:%M:%S"),
                                                      "%Y-%m-%d %H:%M:%S") + timedelta(hours=duration)
            apm.appointment_end = end_date
        return True

    name = fields.Char(string='Appointment #', size=64, default=lambda *a: '/')
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True,
                              states={'Scheduled': [('readonly', False)]})
    doctor = fields.Many2one('sh.medical.physician', string='Physician', help="Current primary care / family doctor",
                             domain=[('is_pharmacist', '=', False)], required=True, readonly=True,
                             states={'Scheduled': [('readonly', False)]}, default=_get_physician)
    appointment_date = fields.Datetime(string='Appointment Date', required=True, readonly=True,
                                       states={'Scheduled': [('readonly', False)]}, default=datetime.datetime.now())
    appointment_end = fields.Datetime(compute=_get_appointment_end, string='Appointment End Date', readonly=True,
                                      states={'Scheduled': [('readonly', False)]})
    duration = fields.Integer(string='Duration (Hours)', readonly=True, states={'Scheduled': [('readonly', False)]},
                              default=lambda *a: 1)
    institution = fields.Many2one('sh.medical.health.center', string='Health Center', help="Medical Center",
                                  readonly=True, states={'Scheduled': [('readonly', False)]})
    urgency_level = fields.Selection(URGENCY_LEVEL, string='Urgency Level', readonly=True,
                                     states={'Scheduled': [('readonly', False)]}, default=lambda *a: 'Normal')
    comments = fields.Text(string='Comments', readonly=True, states={'Scheduled': [('readonly', False)]})
    patient_status = fields.Selection(PATIENT_STATUS, string='Patient Status', readonly=True,
                                      states={'Scheduled': [('readonly', False)]}, default=lambda *a: 'Inpatient')
    state = fields.Selection(APPOINTMENT_STATUS, string='State', readonly=True, default=lambda *a: 'Scheduled')

    # Phiếu tái khám
    evaluation_ids = fields.One2many('sh.medical.evaluation', 'appointment', string='Evaluation', readonly=True,
                                     states={'Scheduled': [('readonly', False)]})

    @api.model
    def create(self, vals):
        if vals.get('doctor') and vals.get('appointment_date'):
            self.check_physician_availability(vals.get('doctor'), vals.get('appointment_date'))

        sequence = self.env['ir.sequence'].next_by_code('sh.medical.appointment')
        vals['name'] = sequence
        health_appointment = super(SHealthAppointment, self).create(vals)
        return health_appointment

    def check_physician_availability(self, doctor, appointment_date):
        available = False
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        patient_line_obj = self.env['sh.medical.physician.line']
        need_to_check_availability = False

        query_doctor_availability = _("select appointment_type from sh_medical_physician where id=%s") % (doctor)
        self.env.cr.execute(query_doctor_availability)
        val = self.env.cr.fetchone()
        if val and val[0]:
            if val[0] == "On Weekly Schedule":
                need_to_check_availability = True

        # check if doctor is working on selected day of the week
        if need_to_check_availability:
            selected_day = datetime.datetime.strptime(appointment_date, DATETIME_FORMAT).strftime('%A')

            if selected_day:
                avail_days = patient_line_obj.search([('name', '=', str(selected_day)), ('physician_id', '=', doctor)],
                                                     limit=1)

                if not avail_days:
                    raise UserError(_('Physician is not available on selected day!'))
                else:
                    # get selected day's start and end time

                    phy_start_time = self.get_time_string(avail_days.start_time).split(':')
                    phy_end_time = self.get_time_string(avail_days.end_time).split(':')

                    user_pool = self.env['res.users']
                    user = user_pool.browse(self.env.uid)
                    tz = pytz.timezone(user.partner_id.tz) or pytz.utc

                    # get localized dates
                    appointment_date = pytz.utc.localize(
                        datetime.datetime.strptime(appointment_date, DATETIME_FORMAT)).astimezone(tz)

                    t1 = datetime.time(int(phy_start_time[0]), int(phy_start_time[1]), 0)
                    t3 = datetime.time(int(phy_end_time[0]), int(phy_end_time[1]), 0)

                    # get appointment hour and minute
                    t2 = datetime.time(appointment_date.hour, appointment_date.minute, 0)

                    if not (t2 > t1 and t2 < t3):
                        raise UserError(_('Physician is not available on selected time!'))
                    else:
                        available = True
        return available

    def get_time_string(self, duration):
        result = ''
        currentHours = int(duration // 1)
        currentMinutes = int(round(duration % 1 * 60))
        if (currentHours <= 9):
            currentHours = "0" + str(currentHours)
        if (currentMinutes <= 9):
            currentMinutes = "0" + str(currentMinutes)
        result = str(currentHours) + ":" + str(currentMinutes)
        return result

    def _default_account(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.default_credit_account_id.id

    def action_appointment_invoice_create(self):
        invoice_obj = self.env["account.move"]
        invoice_line_obj = self.env["account.move.line"]
        inv_ids = []

        for acc in self:
            # Create Invoice
            if acc.patient:
                curr_invoice = {
                    'partner_id': acc.patient.partner_id.id,
                    'account_id': acc.patient.partner_id.property_account_receivable_id.id,
                    'patient': acc.patient.id,
                    'state': 'draft',
                    'type': 'out_invoice',
                    'date_invoice': acc.appointment_date,
                    'origin': "Appointment # : " + acc.name,
                    'sequence_number_next_prefix': False
                }

                inv_ids = invoice_obj.create(curr_invoice)
                inv_id = inv_ids.id

                if inv_ids:
                    prd_account_id = self._default_account()
                    # Create Invoice line
                    curr_invoice_line = {
                        'name': "Consultancy invoice for " + acc.name,
                        'price_unit': acc.doctor.consultancy_price,
                        'quantity': 1,
                        'account_id': prd_account_id,
                        'invoice_id': inv_id,
                    }

                    inv_line_ids = invoice_line_obj.create(curr_invoice_line)

                self.write({'state': 'Invoiced'})
        return {
            'domain': "[('id','=', " + str(inv_id) + ")]",
            'name': _('Appointment Invoice'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window'
        }

    def set_to_completed(self):
        return self.write({'state': 'Completed'})

    def unlink(self):
        for appointment in self.filtered(lambda appointment: appointment.state not in ['Draft']):
            raise UserError(_('You can not delete an appointment which is not in "Draft" state !!'))
        return super(SHealthAppointment, self).unlink()


class SHealthReExamService(models.Model):
    _name = 'sh.medical.prescription.service.reexam'
    _description = "Lịch tái khám theo đơn thuốc"

# Prescription Management  - Đơn thuốc
class SHealthPrescriptions(models.Model):
    _name = 'sh.medical.prescription'
    _description = 'Prescriptions'
    _inherit = ['mail.thread']

    _order = "name"

    STATES = [
        ('Draft', 'Nháp'),
        # ('Invoiced', 'Invoiced'),
        # ('Sent to Pharmacy', 'Sent to Pharmacy'),
        ('Sent to Pharmacy', 'Chờ duyệt'),
        ('Đã xuất thuốc', 'Đã xuất thuốc'),
        ('Cancel', 'Hủy')
    ]

    # Automatically detect logged in physician

    def _get_physician(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain, limit=1)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    def _get_room_stock_out_domain(self):
        grp_loc_dict = {'shealth_all_in_one.group_sh_medical_physician_surgery': 'Surgery',
                        'shealth_all_in_one.group_sh_medical_physician_odontology': 'Odontology',
                        'shealth_all_in_one.group_sh_medical_physician_spa': 'Spa',
                        'shealth_all_in_one.group_sh_medical_physician_laser': 'Laser'}
        ward_types = [False]
        for grp, w_type in grp_loc_dict.items():
            if self.env.user.has_group(grp):
                ward_types.append(w_type)
        domain = "[('institution', '=', institution), ('location_medicine_out_stock', '!=', False), " \
                 "('location_supply_out_stock', '!=', False), ('department.type', 'in', %s)]" % ward_types
        return domain

    name = fields.Char(string='Prescription #', size=64, readonly=True, required=True, default=lambda *a: '/')
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True,
                              states={'Draft': [('readonly', False)]})
    doctor = fields.Many2one('sh.medical.physician', string='Physician', domain=[('is_pharmacist', '=', False)],
                             help="Current primary care / family doctor", required=True, readonly=True,
                             states={'Draft': [('readonly', False)]}, default=_get_physician)
    pharmacy = fields.Many2one('sh.medical.health.center.pharmacy', 'Pharmacy', readonly=True,
                               states={'Draft': [('readonly', False)]})
    location_id = fields.Many2one('stock.location', 'Medicine stock', readonly=True,
                                  states={'Draft': [('readonly', False)]})
    date = fields.Datetime(string='Ngày làm dịch vụ', readonly=False, states={'Đã xuất thuốc': [('readonly', True)]},
                           default=datetime.datetime.now())
    date_out = fields.Datetime(string='Prescription Date out', readonly=False,
                               states={'Đã xuất thuốc': [('readonly', True)]}, default=datetime.datetime.now())
    # info = fields.Text(string='Prescription Notes', readonly=True, states={'Draft': [('readonly', False)]})
    prescription_line = fields.One2many('sh.medical.prescription.line', 'prescription_id', string='Prescription Lines',
                                        readonly=False, states={'Đã xuất thuốc': [('readonly', True)]})
    state = fields.Selection(STATES, 'State', readonly=True, default=lambda *a: 'Draft', tracking=True)

    services = fields.Many2many('sh.medical.health.center.service', 'sh_prescription_service_rel', 'prescription_id',
                                'service_id', track_visibility='onchange', string='Services', readonly=False,
                                states={'Đã xuất thuốc': [('readonly', True)]})

    institution = fields.Many2one('sh.medical.health.center', string='Health Center', required=True, readonly=False,
                                  states={'Đã xuất thuốc': [('readonly', True)]}, track_visibility='onchange')
    his_company = fields.Many2one('res.company', string='Company',
                                  related='institution.his_company')  # dùng để domain location

    #  check công ty hiện tại của người dùng với công ty của phiếu
    check_current_company = fields.Boolean(string='Cty hiện tại', compute='_check_current_company')

    #  domain vật tư và thuốc theo kho của phòng
    supply_domain = fields.Many2many('sh.medical.medicines', string='Supply domain', compute='_get_supply_domain')

    room_request = fields.Many2one('sh.medical.health.center.ot', string='Phòng yêu cầu',
                                   domain="[('institution', '=', institution)]")
    room_stock_out = fields.Many2one('sh.medical.health.center.ot', string='Phòng xuất đơn',
                                     domain=lambda self: self._get_room_stock_out_domain())
    buttons_visible = fields.Boolean(string='Hiện nút xuất thuốc', compute='_get_buttons_visible',
                                     help='Check nếu người dùng hiện tại được thấy nút xuất thuốc')

    diagnose = fields.Text(string='Chẩn đoán(in trên đơn thuốc)')

    # other_bom = fields.Many2many('sh.medical.product.bundle', 'sh_prescription_bom_rel', 'prescription_id', 'bom_id',
    #                              string='All BOM of service',
    #                              domain="[('service_id', 'in', 'services.ids')]")

    REGION = [
        ('North', 'Miền Bắc'),
        ('South', 'Miền Nam')
    ]

    other_bom = fields.Many2one('sh.medical.product.bundle', string='Chọn BOM',
                                domain="[('service_id', 'in', services),('region', '=', region),('type', '=', 'Medicine')]")
    other_bom_ids = fields.Many2many('sh.medical.product.bundle', 'sh_medical_prescription_product_bundle_rel',
                                     string='Danh sách BOM',
                                     domain="[('service_id', 'in', services),('region', '=', region),('type', '=', 'Medicine')]")

    # vùng miền
    region = fields.Selection(REGION, string='Miền', help="Vùng miền", related="institution.region")

    # Phiếu tái khám
    evaluation = fields.Many2one('sh.medical.evaluation', string='Tái khám', ondelete='cascade')

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', ondelete='cascade')
    allow_institutions = fields.Many2many('sh.medical.health.center', string='Allow institutions',
                                          related='walkin.allow_institutions')

    service_related = fields.Many2many('sh.medical.health.center.service', string='Services related',
                                       related='walkin.service')

    @api.onchange('walkin')
    def _onchange_walkin(self):
        if self.walkin:
            self.patient = self.walkin.patient
            # self.chief_complaint = 'Tái khám: %s' % ','.join(self.walkin.service.mapped('name'))
            self.admission_reason_walkin = self.walkin.reason_check
            self.services = [(6, 0, self.walkin.service.filtered(lambda s: not s.is_no_specialty).ids)]

    @api.depends('institution.his_company')
    def _check_current_company(self):
        for record in self:
            record.check_current_company = True if record.institution.his_company == self.env.company else False

    @api.depends('institution.his_company', 'room_stock_out.department.type')
    def _get_buttons_visible(self):
        for record in self:
            record.buttons_visible = False
            if record.institution.his_company == self.env.company:
                if (record.room_stock_out.department.type and self.env.user.has_group(
                        'shealth_all_in_one.group_sh_medical_physician')) \
                        or (not record.room_stock_out.department.type and (
                        self.env.user.has_group('shealth_all_in_one.group_sh_medical_stock_manager'))) \
                        or self.env.user.has_group('shealth_all_in_one.group_sh_medical_manager'):
                    record.buttons_visible = True

    def action_cancel(self):
        if self.state != 'Draft':
            raise ValidationError('Bạn chỉ có thể hủy đơn thuốc này khi đang ở trạng thái Nháp')
        else:
            self.state = 'Cancel'

    # domain chỉ chọn dc các sp còn trong kho
    @api.depends('room_stock_out')
    def _get_supply_domain(self):
        for record in self:
            record.supply_domain = False
            locations = self.room_stock_out.location_medicine_out_stock + self.room_stock_out.location_supply_out_stock
            if locations:
                products = self.env['stock.quant'].search(
                    [('quantity', '>', 0), ('location_id', 'in', locations.ids)]).filtered(
                    lambda q: q.reserved_quantity < q.quantity).mapped('product_id')
                if products:
                    medicines = self.env['sh.medical.medicines'].search([('product_id', 'in', products.ids)])
                    record.supply_domain = [(6, 0, medicines.ids)]

    def reset_all_prescription_line(self):
        for presciption in self.filtered(lambda sp: sp.state not in ['Đã xuất thuốc']):
            presciption.write({
                'prescription_line': False,
                'other_bom_ids': False
            })

    # thay đổi phòng xuất thuốc
    @api.onchange('room_stock_out', 'other_bom_ids')
    def _onchange_room_stock_out(self):
        self.prescription_line = False
        if self.other_bom_ids:
            vals = []
            check_duplicate = []

            for record in self.other_bom_ids:
                for record_line in record.products.filtered(lambda p: p.note == 'Medicine'):
                    location = self.room_stock_out.location_supply_out_stock
                    if record_line.product_id.medicament_type == 'Medicine':
                        location = self.room_stock_out.location_medicine_out_stock
                    if location:
                        qty = record_line.quantity

                        mats_id = record_line.product_id.id
                        if mats_id not in check_duplicate:
                            check_duplicate.append(mats_id)
                            vals.append((0, 0, {'name': mats_id,
                                                'init_qty': qty,
                                                'qty': qty,
                                                'dose_unit_related': record_line.uom_id.id,
                                                'location_id': location.id,
                                                'services': [(4, record.service_id.id)],
                                                'info': record_line.dosage}))
                        else:

                            old_supply_index = check_duplicate.index(mats_id)
                            vals[old_supply_index][2]['services'].append((4, record.service_id.id))
                            vals[old_supply_index][2]['qty'] += qty
                            vals[old_supply_index][2]['init_qty'] += qty
            self.prescription_line = vals
            # Đây là phần tính trung bình số lượng sử dụng theo số dịch vụ
            for medical in self.prescription_line:
                if medical.dose_unit_related.int_rounding:
                    medical.qty = round(medical.qty / len(medical.services))
                    medical.init_qty = round(medical.init_qty / len(medical.services))
                else:
                    medical.qty = medical.qty / len(medical.services)
                    medical.init_qty = medical.init_qty / len(medical.services)

    @api.onchange('date', 'date_out')
    def _onchange_date(self):
        if self.date and self.date_out:
            if self.date > self.date_out:
                raise UserError('Thông tin không hợp lệ! Ngày làm dịch vụ phải trước ngày xuất thuốc!')

    def view_detail_prescriptions(self):
        return {
            'name': _('Chi tiết Đơn thuốc'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_prescription_view').id,
            'res_model': 'sh.medical.prescription',  # model want to display
            'target': 'current',  # if you want popup,
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': self.id
        }

    @api.onchange('date', 'date_out')
    def _onchange_date(self):
        if not self.date_out:
            self.date_out = self.date

        if self.date and self.date_out:
            if self.date > self.date_out:
                raise UserError(
                    _('Thông tin không hợp lệ! Ngày kê đơn phải trước ngày xuất thuốc!'))

    # Function chẩn đoán in trên đơn thuốc
    def get_diagnose(self, code_brand, list_services):
        diagnose = ''
        if list_services and code_brand in ['DA', 'KN']:
            for service in list_services:
                if service.technical_name:
                    diagnose += (service.technical_name + ', ')
        else:
            for service in self.services:
                diagnose += service.name
        return diagnose

    @api.onchange('services')
    def onchange_services(self):
        """
        Lấy tên dịch vụ theo danh mục kỹ thuật in trên đơn thuốc
        """
        self.diagnose = self.get_diagnose(self.institution.his_company.brand_id.code, self.services)
        result_bom_ids = self.env['sh.medical.product.bundle']
        for service in self.services:
            other_bom = self.env['sh.medical.product.bundle'].search(
                [('service_id', '=', service._origin.id), ('type', '=', 'Medicine'),
                 ('region', '=', self.region)], limit=1)
            if other_bom:
                result_bom_ids += other_bom
        self.other_bom_ids = [(6, 0, result_bom_ids.ids)]

    @api.model
    def create(self, vals):
        region = self.env['sh.medical.health.center'].search([('id', '=', vals['institution'])], limit=1).region
        result_bom_ids = self.env['sh.medical.product.bundle']
        if 'services' in vals and vals['services']:
            for service in vals['services'][0][2]:
                other_bom = self.env['sh.medical.product.bundle'].search(
                    [('service_id', '=', service), ('type', '=', 'Medicine'),
                     ('region', '=', region)],
                    limit=1)
                if other_bom:
                    result_bom_ids += other_bom
            vals.update({
                'other_bom_ids': [[6, 0, result_bom_ids.ids]]
            })
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.prescription.%s' % vals['institution'])
        if not sequence:
            raise ValidationError('Định danh Đơn thuốc về của Cơ sở y tế này đang không tồn tại!')
        vals['name'] = sequence
        # chaỵ onchange cho đơn thuốc ở tree view với các trường m2m, o2m
        if vals.get('services') and not (vals.get('prescription_line')):
            Prescriptions = self.env['sh.medical.prescription']
            temp_rec = Prescriptions.new(
                {'services': vals.get('services'), 'date': vals.get('date'), 'patient': vals.get('patient')})
            temp_rec._onchange_services_prescription()
            onchange_vals = temp_rec._convert_to_write(temp_rec._cache)
            for onchange_field in ['prescription_line']:  # add trường được thay đổi vào vals để write
                if onchange_field in onchange_vals.keys():
                    vals[onchange_field] = onchange_vals.get(onchange_field)
        health_prescription = super(SHealthPrescriptions, self).create(vals)
        health_prescription.diagnose = self.get_diagnose(health_prescription.his_company.brand_id.code,
                                                         health_prescription.services)
        return health_prescription

    def write(self, vals):
        if vals.get('date_out') or vals.get('date'):
            for record in self:
                date = vals.get('date') or record.date
                date_out = vals.get('date_out') or record.date_out

                if isinstance(date, str):
                    date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                if isinstance(date_out, str):
                    date_out = datetime.datetime.strptime(date_out, '%Y-%m-%d %H:%M:%S')

                if date and date_out and date > date_out:
                    raise UserError(
                        _(
                            'Thông tin không hợp lệ! Ngày kê đơn phải trước ngày xuất thuốc!'))
        # chaỵ onchange cho đơn thuốc ở tree view với các trường m2m, o2m
        if vals.get('services') and not (vals.get('prescription_line') or vals.get('info') or vals.get('days_reexam')):
            # Khi write service chỉ được write từng bản ghi vì cần thay đổi các trường m2m và o2m từng bản ghi
            self.ensure_one()
            Prescriptions = self.env['sh.medical.prescription']
            temp_rec = Prescriptions.new({'services': vals.get('services'), 'date': vals.get('date') or self.date},
                                         origin=self)
            temp_rec._onchange_services_prescription()
            onchange_vals = temp_rec._convert_to_write(temp_rec._cache)
            for onchange_field in ['prescription_line', 'info',
                                   'days_reexam']:  # add 3 trường được thay đổi vào vals để write
                if onchange_field in onchange_vals.keys():
                    vals[onchange_field] = onchange_vals.get(onchange_field)
        return super(SHealthPrescriptions, self).write(vals)

    def _get_services_data(self):
        self.ensure_one()
        prescription_line = []
        # data_recheck = []
        seq = 0
        # info_data = ''
        id_prescription_line = {}
        for service_done in self.services:
            if service_done.prescription_ids:
                # check đã có thì cộng dồn
                for prescription in service_done.prescription_ids:
                    med_dict_key = str(prescription.product_id.id)
                    med_init_qty_line = prescription.dose_unit._compute_quantity(prescription.qty,
                                                                                 prescription.product_id.uom_id)
                    med_qty_line = prescription.dose_unit._compute_quantity(prescription.qty,
                                                                            prescription.product_id.uom_id)

                    if str(prescription.product_id.id) not in id_prescription_line:
                        seq += 1
                        id_prescription_line[med_dict_key] = seq
                        prescription_line.append((0, 0, {
                            'name': prescription.product_id.id,
                            'patient': self.patient.id,
                            'init_qty': med_init_qty_line,
                            'qty': med_qty_line,
                            'dose': prescription.dose,
                            'dose_unit_related': prescription.product_id.uom_id.id,
                            'common_dosage': prescription.common_dosage.id,
                            'duration': prescription.duration,
                            'duration_period': prescription.duration_period,
                            'is_buy_out': prescription.is_buy_out,
                            'services': [(4, service_done.id)],
                            'info': prescription.note}))
                    else:
                        prescription_line[id_prescription_line[med_dict_key] - 1][2]['init_qty'] += med_init_qty_line
                        prescription_line[id_prescription_line[med_dict_key] - 1][2]['qty'] += med_qty_line
                        prescription_line[id_prescription_line[med_dict_key] - 1][2]['services'] += [
                            (4, service_done.id)]

            # có hướng dẫn chăm sóc và lịch tái khám
            # if service_done.info:
            #     # info_data +='<p style="page-break-before:always;"> </p>' + service_done.info
            #     info_data += service_done.info
            #
            # if service_done.days_reexam:
            #     for rc in service_done.days_reexam:
            #         data_recheck.append((0, 0, {
            #             'name': rc.name,
            #             'after_service_date': rc.after_service_date,
            #             'type': rc.type,
            #             'service_date': self.date,
            #             'date_recheck': (datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
            #                                                         "%Y-%m-%d %H:%M:%S") + timedelta(
            #                 days=rc.after_service_date)).strftime("%Y-%m-%d") or fields.Date.today(),
            #             'for_service': service_done.name
            #         }))
        # return prescription_line, info_data, data_recheck
        return prescription_line

    @api.onchange('services')
    def _onchange_services_prescription(self):
        self.prescription_line = False
        prescription_line = self._get_services_data()

        # self.prescription_line = self.info = self.days_reexam = False
        # prescription_line, info_data, data_recheck = self._get_services_data()
        # đổ data đơn thuốc
        self.prescription_line = prescription_line
        # đổ data hướng dẫn theo dịch vụ
        # self.info = info_data
        # đổ data lịch tái khám
        # self.days_reexam = data_recheck

    def _default_account(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.default_credit_account_id.id

    def action_prescription_invoice_create(self):
        invoice_obj = self.env["account.move"]
        invoice_line_obj = self.env["account.move.line"]
        inv_ids = []

        for pres in self:
            # Create Invoice
            if pres.patient:
                curr_invoice = {
                    'partner_id': pres.patient.partner_id.id,
                    'account_id': pres.patient.partner_id.property_account_receivable_id.id,
                    'patient': pres.patient.id,
                    'state': 'draft',
                    'type': 'out_invoice',
                    'date_invoice': pres.date.strftime('%Y-%m-%d'),
                    'origin': "Prescription# : " + pres.name,
                    'sequence_number_next_prefix': False
                }

                inv_ids = invoice_obj.create(curr_invoice)
                inv_id = inv_ids.id

                if inv_ids:
                    prd_account_id = self._default_account()
                    if pres.prescription_line:
                        for ps in pres.prescription_line:
                            # Create Invoice line
                            curr_invoice_line = {
                                'name': ps.name.product_id.name,
                                'product_id': ps.name.product_id.id,
                                'price_unit': ps.name.product_id.list_price,
                                'quantity': ps.qty,
                                'account_id': prd_account_id,
                                'invoice_id': inv_id,
                            }

                            inv_line_ids = invoice_line_obj.create(curr_invoice_line)

                self.write({'state': 'Invoiced'})

        return {
            'domain': "[('id','=', " + str(inv_id) + ")]",
            'name': 'Prescription Invoice',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window'
        }

    def unlink(self):
        for priscription in self.filtered(lambda priscription: priscription.state not in ['Draft']):
            raise UserError(_('You can not delete a prescription which is not in "Draft" state !!'))
        return super(SHealthPrescriptions, self).unlink()

    # từ nháp sang gửi đơn
    def action_prescription_send_to_pharmacy(self):
        if not self.prescription_line:
            raise UserError(_('Bạn phải nhập ít nhất 1 thuốc cho đơn thuốc!'))

        self.write({'state': 'Sent to Pharmacy'})

    # từ gửi đơn về nháp
    def set_to_draft(self):
        return self.write({'state': 'Draft'})

    # set trạng thái phiếu từ ĐÃ XUẤT THUỐC về trạng thái GỦI ĐƠN
    def set_to_send_pharmacy(self):
        self.reverse_prescription()
        return self.write({'state': 'Sent to Pharmacy'})

    def reverse_prescription(self):
        num_of_location = len(self.prescription_line.mapped('location_id'))
        # num_of_location = 1
        pick_need_reverses = self.env['stock.picking'].search(
            [('origin', 'ilike', 'THBN - THUỐC KÊ ĐƠN - %s - %s' % (self.name, self.walkin.name)),
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

    def check_have_record(self, record):
        if isinstance(record.id, models.NewId):
            res = super(SHealthPrescriptions, self).create({
                'patient': record.patient.id,
                'doctor': record.doctor.id,
                'walkin': record.walkin.id,
                'services': record.services.ids,
                'date': record.date,
                'date_out': record.date_out,
                'prescription_line': record.prescription_line.ids,
                'info': record.info,
            })
            return res
        else:
            return record

    def action_prescription_out(self):

        if (len(self.other_bom_ids) != len(self.services)) and not self.evaluation:
            raise ValidationError('Số lượng BoM phải bằng số lượng dịch vụ')
        # neu data đơn thuốc chưa được tạo thì gọi hàm tạo
        res = self.check_have_record(self)

        if not res.prescription_line:
            raise UserError(_('Bạn phải nhập ít nhất 1 thuốc cho đơn thuốc!'))

        if res.other_bom:
            ids_bom = res.other_bom.products.filtered(lambda p: p.note == 'Medicine').mapped('product_id').ids
            ids_use = res.prescription_line.mapped('name').ids

            if ids_bom != ids_use and (
                    (not self.env.user.has_group('shealth_all_in_one.group_sh_medical_stock_manager')) and (
                    not self.env.user.has_group('shealth_all_in_one.group_sh_medical_stock_user'))):
                raise ValidationError(
                    'Đơn thuốc có sự chênh lệch các đầu mục thuốc, vật tư so với bom định mức! Bạn không có quyền duyệt đơn này! Hãy liên hệ với quản lý Kho Dược hoặc Trưởng Bộ phận để xử lý!')

        # trừ kho theo đơn thuốc xuất
        if res.date_out:
            date_out = res.date_out
        else:
            date_out = fields.Datetime.now()
        if date_out > datetime.datetime.now():
            raise ValidationError('Bạn không thể đóng đơn thuốc do ngày xuất lớn hơn ngày giờ hiện tại!')

        # 20220320 - tungnt - onnet
        default_production_location = self.env['stock.location'].get_default_production_location_per_company()

        vals = {}
        validate_str = ''
        for medicine in res.prescription_line:
            # nếu thuốc này ko mua ngoài
            if not medicine.is_buy_out:
                # nếu có chỉnh sửa số lượng thì ko dc duyệt, chỉ quyền quản lý kho dược và quản lý tủ trực được duyệt
                if medicine.qty != medicine.init_qty and (
                        (not self.env.user.has_group('shealth_all_in_one.group_sh_medical_stock_manager')) and (
                        not self.env.user.has_group('shealth_all_in_one.group_sh_medical_stock_user'))):
                    raise ValidationError(_(
                        "Đơn thuốc có chỉnh sửa so với định mức! Bạn không có quyền duyệt đơn này! Hãy liên hệ với quản lý Kho Dược hoặc Trưởng Bộ phận để xử lý!"))
                if medicine.qty > 0:  # CHECK SO LUONG SU DUNG > 0
                    quantity_on_hand = self.env['stock.quant']._get_available_quantity(medicine.name.product_id,
                                                                                       medicine.location_id)  # check quantity trong location
                    if medicine.dose_unit_related != medicine.name.product_id.uom_id:
                        medicine.write({'qty': medicine.dose_unit_related._compute_quantity(medicine.qty,
                                                                                            medicine.name.product_id.uom_id),
                                        'dose_unit_related': medicine.name.product_id.uom_id})  # quy so suong su dung ve don vi chinh cua san pham

                    if quantity_on_hand < medicine.qty:
                        validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
                            medicine.name.product_id.default_code, medicine.name.product_id.name, str(quantity_on_hand),
                            str(medicine.dose_unit_related.name), medicine.location_id.name)
                    else:  # truong one2many trong stock picking de tru cac product trong inventory
                        sub_vals = {
                            'name': 'THBN - THUỐC KÊ ĐƠN: ' + medicine.name.product_id.name,
                            'origin': res.name,
                            'date': date_out,
                            'company_id': self.env.company.id,
                            'date_expected': date_out,
                            'product_id': medicine.name.product_id.id,
                            'product_uom_qty': medicine.qty,
                            'product_uom': medicine.dose_unit_related.id,
                            'location_id': medicine.location_id.id,
                            'location_dest_id': default_production_location.id,
                            'partner_id': res.patient.partner_id.id,
                            # xuat cho khach hang/benh nhan nao

                            'material_line_object': medicine._name,
                            'material_line_object_id': medicine.id,
                        }
                        if not vals.get(str(medicine.location_id.id)):
                            vals[str(medicine.location_id.id)] = [sub_vals]
                        else:
                            vals[str(medicine.location_id.id)].append(sub_vals)

        # neu co data thuoc
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
                pick_note = 'THBN - THUỐC KÊ ĐƠN - %s - %s - %s' % (
                    res.name, res.walkin.name, location_key)
                pick_vals = {'note': pick_note,
                             'origin': pick_note,
                             'partner_id': res.patient.partner_id.id,
                             'patient_id': res.patient.id,
                             'picking_type_id': picking_type,
                             'location_id': int(location_key),
                             'location_dest_id': default_production_location.id,
                             # xuat cho khach hang/benh nhan nao
                             'date_done': date_out,
                             # 'immediate_transfer': True,  # sẽ gây lỗi khi dùng lô, pick với immediate_transfer sẽ ko cho tạo move, chỉ tạo move line
                             # 'move_ids_without_package': vals[location_key]
                             }
                fail_pick_name = self.env['stock.picking'].search(
                    [('origin', 'ilike',
                      'THBN - THUỐC KÊ ĐƠN - %s - %s - %s' % (res.name, res.walkin.name, location_key))],
                    limit=1).name
                if fail_pick_name:
                    pick_vals['name'] = fail_pick_name.split('-', 1)[0]
                stock_picking = self.env['stock.picking'].create(pick_vals)
                for move_val in vals[location_key]:
                    move_val['name'] = stock_picking.name + " - " + move_val['name']
                    move_val['picking_id'] = stock_picking.id
                    self.env['stock.move'].create(move_val)

                # TU DONG XUAT KHO
                stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
                for move_line in stock_picking.move_ids_without_package:  # set so luong done
                    for move_live_detail in move_line.move_line_ids:
                        move_live_detail.qty_done = move_live_detail.product_uom_qty
                    # move_line.quantity_done = move_line.product_uom_qty
                stock_picking.with_context(
                    force_period_date=date_out).sudo().button_validate()  # ham tru product trong inventory, sudo để đọc stock.valuation.layer

                # sua ngay hoan thanh
                for move_line in stock_picking.move_ids_without_package:
                    move_line.move_line_ids.write(
                        {'date': date_out})  # sửa ngày hoàn thành ở stock move line
                stock_picking.move_ids_without_package.write(
                    {'date': date_out})  # sửa ngày hoàn thành ở stock move

                stock_picking.date_done = date_out
                stock_picking.sci_date_done = date_out
                stock_picking.create_date = res.date
                # Cập nhật ngược lại picking_id vào mats để truyền số liệu sang vật tư phiếu khám
                res.prescription_line.filtered(lambda p: p.location_id.id == int(location_key)).write(
                    {'picking_id': stock_picking.id})

        elif validate_str != '':
            raise ValidationError(_(
                "Các loại Thuốc sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))

        res.write({'state': 'Đã xuất thuốc', 'date_out': date_out})

        # cập nhật vtth phiếu khám
        res.walkin.update_walkin_material(mats_types=['Medicine'])

        # return {'type': 'ir.actions.client',
        #     'tag': 'reload'}

    # def action_prescription_out_admin(self):
    #     # Tách hàm riêng cho quản lý csyt để sau này thêm điều kiện
    #     return self.action_prescription_out()
    #
    # def action_prescription_out_stock_manager(self):
    #     # Tách hàm riêng cho quản lý kho dược để sau này thêm điều kiện
    #     return self.action_prescription_out()
    #
    # def action_prescription_out_room_manager(self):
    #     # Tách hàm riêng cho quản lý phòng dịch vụ để sau này thêm điều kiện
    #     return self.action_prescription_out()

    def print_patient_prescription(self):
        return self.env.ref('shealth_all_in_one.action_sh_medical_report_patient_prescriptions_10').report_action(self)

    # def print_patient_huongdan(self):
    #     return self.env.ref('shealth_all_in_one.action_sh_medical_report_patient_prescriptions_huongdan').report_action(self)


class SHealthPrescriptionLines(models.Model):
    _name = 'sh.medical.prescription.line'
    _description = 'Prescription Lines'
    _order = 'sequence'

    FREQUENCY_UNIT = [
        ('Seconds', 'Seconds'),
        ('Minutes', 'Minutes'),
        ('Hours', 'Hours'),
        ('Days', 'Days'),
        ('Weeks', 'Weeks'),
        ('When Required', 'When Required'),
    ]

    DURATION_UNIT = [
        ('Minutes', 'Minutes'),
        ('Hours', 'Hours'),
        ('Days', 'Days'),
        ('Months', 'Months'),
        ('Years', 'Years'),
        ('Indefinite', 'Indefinite'),
    ]

    sequence = fields.Integer(default=10)
    prescription_id = fields.Many2one('sh.medical.prescription', string='Prescription Reference', required=True,
                                      ondelete='cascade', index=True)
    name = fields.Many2one('sh.medical.medicines', string='Medicines', help="Prescribed Medicines",
                           domain=[('medicament_type', '=', 'Medicine')], required=True)
    indication = fields.Many2one('sh.medical.pathology', string='Indication',
                                 help="Choose a disease for this medicament from the disease list. It can be an existing disease of the patient or a prophylactic.")
    dose = fields.Float(string='Dose', help="Amount of medicines (eg, 250 mg ) each time the patient takes it")
    # dose_unit_related = fields.Many2one('uom.uom', 'Unit of Measure')
    dose_unit_related = fields.Many2one('uom.uom', string='Liều dùng', related='name.uom_id',
                                        help="Amount of medicines (eg, 250 mg ) each time the patient takes it")
    dose_unit = fields.Many2one('sh.medical.dose.unit', string='Dose Unit',
                                help="Unit of measure for the medication to be taken")
    dose_route = fields.Many2one('sh.medical.drug.route', string='Administration Route',
                                 help="HL7 or other standard drug administration route code.")
    dose_form = fields.Many2one('sh.medical.drug.form', 'Form', help="Drug form, such as tablet or gel")
    qty = fields.Float(string='x', help="Quantity of units (eg, 2 capsules) of the medicament", default=lambda *a: 1.0)
    init_qty = fields.Float(string='Số lượng định mức', help="Số lượng mặc định ban đầu theo dịch vụ",
                            default=lambda *a: 0.0)

    qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
                             compute='compute_available_qty_supply')
    qty_in_loc = fields.Float(string='Số lượng tại tủ', required=True, help="Số lượng khả dụng trong tủ trực",
                              compute='compute_available_qty_supply_in_location')
    is_warning_location = fields.Boolean('Cảnh báo tại tủ', compute='compute_available_qty_supply_in_location')

    location_id = fields.Many2one('stock.location', 'Stock location')

    common_dosage = fields.Many2one('sh.medical.dosage', string='Frequency',
                                    help="Common / standard dosage frequency for this medicines")
    frequency = fields.Integer('Số lần dùng')
    frequency_unit = fields.Selection(FREQUENCY_UNIT, 'Unit', index=True)
    admin_times = fields.Char(string='Admin hours', size=128,
                              help='Suggested administration hours. For example, at 08:00, 13:00 and 18:00 can be encoded like 08 13 18')
    duration = fields.Integer(string='Treatment duration')
    duration_period = fields.Selection(DURATION_UNIT, string='Treatment period',
                                       help="Period that the patient must take the medication. in minutes, hours, days, months, years or indefinately",
                                       index=True)
    start_treatment = fields.Datetime(string='Start of treatment')
    end_treatment = fields.Datetime('End of treatment')
    info = fields.Text('Comment')
    is_buy_out = fields.Boolean('Mua ngoài', default=False)
    patient = fields.Many2one('sh.medical.patient', 'Patient', help="Patient Name")

    services = fields.Many2many('sh.medical.health.center.service', 'sh_prescription_line_service_rel',
                                track_visibility='onchange',
                                string='Dịch vụ thực hiện')
    service_related = fields.Many2many('sh.medical.health.center.service', 'sh_prescription_line_service_related_rel',
                                       related="prescription_id.services",
                                       string='Dịch vụ liên quan')

    note = fields.Text('Ghi chú')
    is_diff_bom = fields.Boolean('Khác định mức?', compute='compute_qty_used_bom')

    picking_id = fields.Many2one('stock.picking', string='Phiếu điều chuyển')

    MEDICAMENT_TYPE = [
        ('Medicine', 'Medicine'),
        ('Supplies', 'Supplies'),
        ('CCDC', 'CCDC')
    ]

    medicament_type = fields.Selection(MEDICAMENT_TYPE, related="name.medicament_type", string='Loại',
                                       store=True)

    @api.depends('qty', 'init_qty')
    def compute_qty_used_bom(self):
        for record in self:
            if record.qty > record.init_qty:
                record.is_diff_bom = True
            else:
                record.is_diff_bom = False

    @api.depends('name', 'dose_unit_related')
    def compute_available_qty_supply(self):  # so luong kha dung toan vien
        for record in self:
            if record.name:
                record.qty_avail = record.dose_unit_related._compute_quantity(record.name.qty_available,
                                                                              record.name.uom_id) if record.dose_unit_related != record.name.uom_id else record.name.qty_available
            else:
                record.qty_avail = 0

    @api.depends('name', 'location_id', 'qty', 'dose_unit_related')
    def compute_available_qty_supply_in_location(self):  # so luong kha dung tai tu
        for record in self:
            if record.name:

                quantity_on_hand = self.env['stock.quant'].sudo()._get_available_quantity(record.name.product_id,
                                                                                          record.location_id)
                record.qty_in_loc = record.dose_unit_related._compute_quantity(quantity_on_hand,
                                                                               record.name.uom_id) if record.dose_unit_related != record.name.uom_id else quantity_on_hand
            else:
                record.qty_in_loc = 0

            record.is_warning_location = True if record.qty > record.qty_in_loc else False

    @api.onchange('qty', 'name')
    def onchange_qty_name(self):
        if self.qty < 0 and self.name:
            raise UserError(_("Số lượng nhập phải lớn hơn 0!"))

    # @api.onchange('name')
    # def onchange_name(self):
    #     if self.prescription_id.services:
    #         self.services = self.prescription_id.services

    @api.onchange('name')
    def onchange_name(self):
        self.info = self.name.dosage
        self.dose_unit_related = self.name.uom_id
        nhom_khang_sinh = self.env['sh.medical.medicines.category'].search([('name', 'like', 'KHÁNG SINH')])
        if self.name.medicine_category_id == nhom_khang_sinh[0]:
            self.sequence = 0
        # mặc định dịch vụ theo phiếu
        self.services = self.prescription_id.services
        # self.location_id = self.prescription_id.location_id.id

        domain = {'domain': {'uom_id': [('category_id', '=', self.name.uom_id.category_id.id)]}}
        if self.medicament_type == 'Medicine':
            self.location_id = self.prescription_id.room_stock_out.location_medicine_out_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'medicine'),
                                               ('company_id', '=', self.prescription_id.institution.his_company.id)]
        elif self.medicament_type == 'Supplies':
            self.location_id = self.prescription_id.room_stock_out.location_supply_out_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'supply'),
                                               ('company_id', '=', self.prescription_id.institution.his_company.id)]

        return domain


# Vaccines Management
class SHealthVaccines(models.Model):
    _name = 'sh.medical.vaccines'
    _description = 'Vaccines'

    # Automatically detect logged in physician

    def _get_physician(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain, limit=1)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    name = fields.Many2one('sh.medical.medicines', string='Vaccine', domain=[('medicament_type', '=', 'Vaccine')],
                           required=True)
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True)
    doctor = fields.Many2one('sh.medical.physician', string='Physician', domain=[('is_pharmacist', '=', False)],
                             help="Current primary care / family doctor", required=True, default=_get_physician)
    date = fields.Datetime(string='Date', required=True, default=datetime.datetime.now())
    institution = fields.Many2one('sh.medical.health.center', string='Institution',
                                  help="Health Center where the patient is being or was vaccinated")
    dose = fields.Integer(string='Dose #', default=lambda *a: 1)
    info = fields.Text('Observation')

    @api.onchange('patient', 'name')
    def onchange_patient(self):
        res = {}
        if self.patient and self.name:
            dose = 0
            query = _("select max(dose) from sh_medical_vaccines where patient=%s and name=%s") % (
                str(self.patient.id), str(self.name.id))
            self.env.cr.execute(query)
            val = self.env.cr.fetchone()
            if val and val[0]:
                dose = int(val[0]) + 1
            else:
                dose = 1
            self.dose = dose
        return res


class Location(models.Model):
    _inherit = "stock.location"

    def should_bypass_reservation(self):
        self.ensure_one()
        # check neu mo lai phieu => trả vt về kho thì sẽ pass qua luôn để lấy dc data lô
        # flag = self.env.context.get('reopen_flag')
        # print(flag)
        # print(self.usage in ('supplier', 'inventory', 'production') or self.scrap_location)
        # if flag:
        #     return self.usage in ('supplier', 'inventory', 'production') or self.scrap_location
        # else:
        #     return self.usage in ('supplier', 'customer', 'inventory', 'production') or self.scrap_location
        # print(self.usage in ('supplier', 'inventory', 'production') or self.scrap_location)
        return self.usage in ('supplier', 'inventory', 'production') or self.scrap_location


# HƯỚNG DẪN CHĂM SÓC SAU DỊCH VỤ
# ReExam Management
class SHealthReExam(models.Model):
    _name = 'sh.medical.reexam'
    _description = 'Lịch tái khám'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _order = "date"

    STATES = [
        ('Draft', 'Nháp'),
        ('Confirmed', 'Đã xác nhận'),
    ]

    name = fields.Char(string='Lịch #', size=64, readonly=True, required=True, default=lambda *a: '/')
    company = fields.Many2one('res.company', string='Chi nhánh chăm sóc')
    patient = fields.Many2one('sh.medical.patient', string='Bệnh nhân', help="Tên bệnh nhân", required=True,
                              readonly=True, states={'Draft': [('readonly', False)]})
    date = fields.Datetime(string='Ngày làm dịch vụ', readonly=False, states={'Confirmed': [('readonly', True)]},
                           default=datetime.datetime.now(), tracking=True)
    date_out = fields.Datetime(string='Ngày ra viện', readonly=False, states={'Confirmed': [('readonly', True)]},
                               tracking=True)
    info = fields.Text(string='Hướng dẫn chăm sóc', readonly=True, states={'Draft': [('readonly', False)]},
                       tracking=True)
    state = fields.Selection(STATES, 'Trạng thái', readonly=True, default=lambda *a: 'Draft', tracking=True)
    end_service = fields.Boolean('Kết thúc liệu trình?', default=False, tracking=True)
    services = fields.Many2many('sh.medical.health.center.service', 'sh_walkin_reexam_service_rel', 'reexam_id',
                                'service_id', track_visibility='onchange', string='Dịch vụ', readonly=False,
                                states={'Confirmed': [('readonly', True)]}, tracking=True)

    days_reexam = fields.One2many('sh.medical.walkin.service.reexam', 'reexam_id', string='Lịch tái khám')

    days_reexam_print = fields.One2many('sh.medical.walkin.service.reexam', 'reexam_id', string='Lịch tái khám',
                                        domain=[('is_print', '=', True)])
    days_reexam_phone = fields.One2many('sh.medical.walkin.service.reexam', 'reexam_id', string='Phone Call chăm sóc',
                                        domain=[('is_phonecall', '=', True)])
    days_reexam_sms = fields.One2many('sh.medical.walkin.service.reexam', 'reexam_id', string='SMS chăm sóc',
                                      domain=[('is_sms', '=', True)])
    company = fields.Many2one('res.company', string='Chi nhánh chăm sóc', states={'Confirmed': [('readonly', True)]})

    def write(self, vals):
        res = super(SHealthReExam, self).write(vals)
        days_reexam_print = self.days_reexam_print.filtered(lambda r: r.system == False)
        for day_reexam_print in days_reexam_print:
            day_reexam_print.write({
                'is_phonecall': True,
                'name_phone': day_reexam_print.name,
                'type_date': day_reexam_print.type_date,
                'after_service_phone_date': day_reexam_print.after_service_date - 1,
                'date_recheck_phone': (self.date_out + timedelta(
                                days=day_reexam_print.after_service_date - 1)) if self.date_out else None,
                'type': day_reexam_print.type,
                'care_type': day_reexam_print.care_type,
            })
        return res


    @api.onchange('date', 'date_out')
    def _onchange_date_out(self):
        if self.date and self.date_out:
            if self.date_out < self.date:
                raise UserError(
                    _('Thông tin không hợp lệ! Ngày ra viện phải lớn hơn ngày ra viện!'))

    @api.onchange('services')
    def _onchange_services_reexam(self):
        self.info = self.days_reexam = self.days_reexam_phone = self.days_reexam_sms = self.days_reexam_print = False
        info_data = ""
        data_recheck = []
        my_dict = {}
        for service_done in self.services:
            # có hướng dẫn chăm sóc và lịch tái khám
            if service_done.info:
                # info_data +='<p style="page-break-before:always;"> </p>' + service_done.info
                info_data += service_done.info
            crm_line = self.walkin.booking_id.crm_line_ids
            quantity = 0
            number_used = 0
            is_treatment = False
            so_line = self.walkin.sale_order_id.order_line
            crm_line_id = 0
            for item in so_line:
                if item.product_id.code == service_done.default_code:
                    crm_line_id = item.crm_line_id.id
                    break
            for item in crm_line:
                if item.id == crm_line_id:
                    quantity = item.quantity
                    number_used = item.number_used + 1
                    is_treatment = item.is_treatment
                    break
            if self.end_service:
                number_used = quantity

            if quantity > 1:
                if number_used == quantity:
                    data_reexam = service_done.days_reexam_eoc
                else:
                    data_reexam = service_done.days_reexam_LT
            else:
                if is_treatment:
                    if self.end_service:
                        data_reexam = service_done.days_reexam_eoc
                    else:
                        data_reexam = service_done.days_reexam_LT
                else:
                    data_reexam = service_done.days_reexam

            for item in data_reexam:
                if my_dict.get(item.code):
                    obj = my_dict[item.code]
                    obj['for_service'] = obj['for_service'] + ' | ' + service_done.name
                    obj['for_service_phone'].append((4, service_done.id))
                else:
                    af_phone = item.after_service_date
                    if item.is_phonecall and item.is_print:
                        af_phone = item.after_service_date - 1
                    if item.type_date == 'm':
                        my_dict[item.code] = {
                            'name': item.name,
                            'name_phone': item.name,
                            'name_sms': 'Nhắc lịch tái khám',
                            'after_service_date': item.after_service_date,
                            'after_service_phone_date': af_phone,
                            'after_service_sms_date': 1,
                            'type': item.type,
                            'care_type': service_done.his_service_type if service_done.his_service_type != 'ChiPhi' else 'DVKH',
                            'type_date': item.type_date,
                            'service_date': self.date_out if self.date_out else None,
                            'date_recheck_print': (self.date_out + timedelta(
                                days=item.after_service_date)) if self.date_out else None,
                            'date_recheck_phone': (self.date_out + timedelta(
                                days=af_phone)) if self.date_out else None,
                            'date_recheck_sms': (self.date_out + timedelta(days=1)).replace(
                                hour=2) if self.date_out else None,
                            'for_service': service_done.name,
                            'for_service_phone': [(4, service_done.id)],
                            'for_service_sms': service_done.name,
                            'is_sms': False,
                            'is_phonecall': item.is_phonecall,
                            'is_print': item.is_print,
                            'system': True
                        }
                    else:
                        my_dict[item.code] = {
                            'name': item.name,
                            'name_phone': item.name,
                            'name_sms': 'Nhắc lịch tái khám',
                            'after_service_date': item.after_service_date,
                            'after_service_phone_date': af_phone,
                            'after_service_sms_date': 1,
                            'type': item.type,
                            'care_type': service_done.his_service_type if service_done.his_service_type != 'ChiPhi' else 'DVKH',
                            'type_date': item.type_date,
                            'service_date': self.date,
                            'date_recheck_print': (self.date + timedelta(
                                days=item.after_service_date)) or fields.Date.today(),
                            'date_recheck_phone': (self.date + timedelta(
                                days=af_phone)) or fields.Date.today(),
                            'date_recheck_sms': (self.date + timedelta(days=1)).replace(hour=2) or fields.Date.today(),
                            'for_service': service_done.name,
                            'for_service_phone': [(4, service_done.id)],
                            'for_service_sms': service_done.name,
                            'is_sms': False,
                            'is_phonecall': item.is_phonecall,
                            'is_print': item.is_print,
                            'system': True
                        }
        for key in my_dict:
            data_recheck.append((0, 0, my_dict[key]))

        # đổ data hướng dẫn theo dịch vụ
        self.info = info_data
        # đổ data lịch tái khám
        self.days_reexam = data_recheck

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.walkin.reexam')
        vals['name'] = sequence
        # chaỵ onchange cho đơn thuốc ở tree view với các trường m2m, o2m
        if vals.get('services') and not (vals.get('info') or vals.get('days_reexam')):
            ReExam = self.env['sh.medical.reexam']
            temp_rec = ReExam.new(
                {'services': vals.get('services'), 'date': vals.get('date'), 'date_out': vals.get('date_out'),
                 'patient': vals.get('patient'),
                 'walkin': vals.get('walkin'), 'end_service': vals.get('end_service')})
            temp_rec._onchange_services_reexam()
            onchange_vals = temp_rec._convert_to_write(temp_rec._cache)
            for onchange_field in ['info',
                                   'days_reexam']:  # add 2 trường được thay đổi vào vals để write
                if onchange_field in onchange_vals.keys():
                    vals[onchange_field] = onchange_vals.get(onchange_field)
        health_reexam = super(SHealthReExam, self.sudo()).create(vals)
        return health_reexam

    def unlink(self):
        for reexam in self.filtered(lambda reexam: reexam.state not in ['Draft']):
            raise UserError(_('Bạn không thể xóa hướng dẫn chăm sóc đã được xác nhận!!'))
        return super(SHealthReExam, self).unlink()

    def action_confirm_reexam(self):
        # gửi SMS cám ơn KH làm DV: đẩy id lịch tái khám vào trường id_reexam
        script_sms = self.company.script_sms_id
        for item in script_sms:
            if item.run:
                if item.type == 'COKHLDV':
                    content_sms = item.content.replace('[Ten_KH]', self.walkin.patient.name)
                    content_sms = content_sms.replace('[Ma_Booking]', self.walkin.booking_id.name)
                    content_sms = content_sms.replace('[Booking_Date]',
                                                      self.walkin.booking_id.booking_date.strftime('%d-%m-%Y'))
                    content_sms = content_sms.replace('[Location_Shop]', self.company.location_shop)
                    content_sms = content_sms.replace('[Ban_Do]', self.company.map_shop)
                    if self.company.health_declaration:
                        content_sms = content_sms.replace('[Khai_Bao]', self.company.health_declaration)

                    crm_sms_vals = []

                    # if item.has_zns:
                    #     # TODO cấu hình trong setting
                    #     # Cảm ơn sau DV: 7158
                    #     content_zns = {
                    #         'template_id': 7158,
                    #         'params': {
                    #             # "ma_booking": self.walkin.booking_id.name,
                    #             # Cấu hình trong template là ma_kh
                    #             "ma_kh": self.walkin.booking_id.name,
                    #             "customer_name": self.walkin.booking_id.contact_name,
                    #             "booking_date": self.walkin.booking_id.booking_date.strftime('%d/%m/%Y')
                    #         }
                    #     }
                    #     zns = {
                    #         'name': 'Cảm ơn Khách hàng làm dịch vụ',
                    #         'contact_name': self.walkin.booking_id.contact_name,
                    #         'partner_id': self.walkin.booking_id.partner_id.id,
                    #         'phone': self.walkin.booking_id.phone,
                    #         'company_id': self.company.id,
                    #         'company2_id': [(6, 0, self.walkin.booking_id.company2_id.ids)],
                    #         'crm_id': self.walkin.booking_id.id,
                    #         'send_date': (self.date_out + timedelta(days=1)).replace(hour=1, minute=0, second=0),
                    #         'desc': json.dumps(content_zns),
                    #         'id_reexam': self.id,
                    #         'type': 'zns',
                    #     }
                    #     crm_sms_vals.append(zns)

                    sms = {
                        'name': 'Cảm ơn Khách hàng làm dịch vụ',
                        'contact_name': self.walkin.booking_id.contact_name,
                        'partner_id': self.walkin.booking_id.partner_id.id,
                        'phone': self.walkin.booking_id.phone,
                        'company_id': self.company.id,
                        'company2_id': [(6, 0, self.walkin.booking_id.company2_id.ids)],
                        'crm_id': self.walkin.booking_id.id,
                        'send_date': (self.date_out + timedelta(days=1)).replace(hour=1, minute=0, second=0),
                        'desc': content_sms,
                        'id_reexam': self.id
                    }
                    crm_sms_vals.append(sms)
                    self.env['crm.sms'].sudo().create(crm_sms_vals)

        # viết đoạn sinh phonecall ở đây
        for item in self.days_reexam:
            if item.is_phonecall:
                pc = self.env['crm.phone.call'].search([('id_reexam', '=', item.id), ('state', '=', 'cancelled')],
                                                       limit=1)
                if pc:
                    pc.write({
                        'state': 'draft',
                        'name': item.name_phone,
                        'call_date': item.date_recheck_phone,
                        'desc': item.for_service_sms,
                        'service_id': item.for_service_phone,
                        'type_pc': item.type,
                        'care_type': item.care_type,
                        'confirm_reexam': True,
                        'company_id': self.company.id
                    })
                else:
                    self.env['crm.phone.call'].sudo().create({
                        'name': item.name_phone,
                        'subject': 'Chăm sóc sau dịch vụ khách hàng - %s' % self.walkin.booking_id.name,
                        'partner_id': self.walkin.booking_id.partner_id.id,
                        'phone': self.walkin.booking_id.phone,
                        'direction': 'out',
                        'company_id': self.company.id,
                        'crm_id': self.walkin.booking_id.id,
                        'order_id': self.walkin.sale_order_id.id,
                        'service_id': item.for_service_phone,
                        'care_type': item.care_type,
                        'medical_id': self.walkin.id,
                        'country_id': self.walkin.booking_id.country_id.id,
                        'street': self.walkin.booking_id.street,
                        'type_crm_id': self.env.ref('crm_base.type_phone_call_after_service_care').id,
                        'date_out_location': self.date_out,
                        'date': self.date,
                        'booking_date': item.date_recheck_phone + timedelta(days=1),
                        'call_date': item.date_recheck_phone,
                        'type_pc': item.type,
                        'confirm_reexam': True,
                        'id_reexam': item.id
                    })
            # check sinh sms tái khám
            # if item.type in ['ReCheck4', 'ReCheck5', 'ReCheck6', 'ReCheck7', 'ReCheck8']:
            #     self.env['crm.sms'].sudo().create({
            #         'name': item.name_sms + ' - %s' % self.walkin.booking_id.name,
            #         'contact_name': self.walkin.booking_id.contact_name,
            #         'partner_id': self.walkin.booking_id.partner_id.id,
            #         'phone': self.walkin.booking_id.phone,
            #         'company_id': self.company.id,
            #         'company2_id': [(6, 0, self.walkin.booking_id.company2_id.ids)],
            #         'crm_id': self.walkin.booking_id.id,
            #         'send_date': item.date_recheck_print - timedelta(days=1),
            #         'desc': item.for_service_sms,
            #         'id_reexam': item.id
            #     })
            if item.is_sms:
                # check sinh sms theo chăm sóc
                sms = self.env['crm.sms'].search([('id_reexam', '=', item.id), ('state', '=', 'cancelled')], limit=1)
                if sms:
                    sms.write({
                        'state': 'draft',
                        'send_date': item.date_recheck_sms,
                        'desc': item.for_service_sms,
                        'company_id': self.company.id,
                    })
                else:
                    self.env['crm.sms'].sudo().create({
                        'name': item.name_sms + ' - %s' % self.walkin.booking_id.name,
                        'contact_name': self.walkin.booking_id.contact_name,
                        'partner_id': self.walkin.booking_id.partner_id.id,
                        'phone': self.walkin.booking_id.phone,
                        'company_id': self.company.id,
                        'company2_id': [(6, 0, self.walkin.booking_id.company2_id.ids)],
                        'crm_id': self.walkin.booking_id.id,
                        'send_date': item.date_recheck_sms,
                        'desc': item.for_service_sms,
                        'id_reexam': item.id
                    })
        # Nếu có tick kết thúc liệu trình , trạng thái của các dịch vụ này trên BK sẽ là kết thúc
        if self.end_service:
            so = self.walkin.sale_order_id
            for so_line in so.order_line:
                if (so_line.crm_line_id.service_id in self.services) and so_line.crm_line_id.is_treatment:
                    so_line.crm_line_id.write({
                        'stage': 'done'
                    })
        return self.write({'state': 'Confirmed'})

    def set_to_cancelled(self):
        for item in self.days_reexam:
            pc = self.env['crm.phone.call'].search([('id_reexam', '=', item.id), ('state', '=', 'draft')])
            for p in pc:
                p.state = 'cancelled'
            sms = self.env['crm.sms'].search([('id_reexam', '=', item.id), ('state', '=', 'draft')])
            for s in sms:
                s.state = 'cancelled'
        # tìm SMS cảm ơn: đẩy id lịch tái khám vào trường id_reexam
        sms = self.env['crm.sms'].search([('id_reexam', '=', self.id), ('state', '=', 'draft')])
        for rec_sms in sms:
            rec_sms.state = 'cancelled'
        # Nếu có tick kết thúc liệu trình , trạng thái của các dịch vụ này trên BK sẽ là kết thúc
        if self.end_service:
            so = self.walkin.sale_order_id
            for so_line in so.order_line:
                if so_line.crm_line_id.service_id in self.services:
                    so_line.crm_line_id.write({
                        'stage': 'processing'
                    })
        return self.write({'state': 'Draft'})

    def print_patient_huongdan(self):
        return self.env.ref('shealth_all_in_one.action_sh_medical_report_patient_reexam_huongdan').report_action(self)

    def view_detail_reexam(self):
        return {
            'name': _('Chi tiết Lịch chăm sóc'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_reexam_view').id,
            'res_model': 'sh.medical.reexam',  # model want to display
            'target': 'current',  # if you want popup,
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': self.id
        }
