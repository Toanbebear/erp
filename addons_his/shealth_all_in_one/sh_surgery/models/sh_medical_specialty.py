# -*- encoding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError, Warning
import calendar
import time
import datetime
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class SHealthSpecialtyTeam(models.Model):
    _name = "sh.medical.specialty.team"
    _description = "Specialty Team"

    # _sql_constraints = [('name_unique', 'unique(name,team_member,service_performances,role)',
    #                      "Vai trò của thành viên với dịch vụ phải là duy nhất!")]

    @api.constrains('name', 'team_member', 'service_performances', 'role')
    def _check_constrains_team_member(self):
        for rec in self:
            similars = self.env['sh.medical.specialty.team'].search(
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
            return [('type', 'in', ['spa', 'laser', 'odontology'])]

    name = fields.Many2one('sh.medical.specialty', string='Specialty')
    team_member = fields.Many2one('sh.medical.physician', string='Thành viên',
                                  help="Health professional that participated on this surgery",
                                  domain=[('is_pharmacist', '=', False)], required=True)

    service_performance = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ thực hiện',
                                          help="Service that persons participated on this surgery")

    service_performances = fields.Many2many('sh.medical.health.center.service', 'sh_specialty_team_services_rel',
                                            'specialty_team_id',
                                            'service_id', string='Dịch vụ thực hiện',
                                            help="Các dịch vụ của thành viên với vai trog này thực hiện")
    role = fields.Many2one('sh.medical.team.role', string='Vai trò', domain=lambda self: self.get_domain_role())
    notes = fields.Char(string='Notes')


# CHUYEN KHOA: DA LIEU, RANG HAM MAT ...
class SHealthSpecialtySupply(models.Model):
    _name = "sh.medical.specialty.supply"
    _description = "Supplies related to the services in specialty"

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

    name = fields.Many2one('sh.medical.specialty', string='Specialty')
    qty = fields.Float(string='Initial required quantity', digits='Product Unit of Measure', required=True,
                       help="Initial required quantity", default=lambda *a: 0)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    supply = fields.Many2one('sh.medical.medicines', string='Supply', required=True,
                             help="Supply to be used in this services in specialty", domain=lambda self: [
            ('categ_id', 'child_of', self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    notes = fields.Char(string='Notes')
    explanation_supply = fields.Selection(EXPLANATION_SUPPLY, string='Giải trình')
    is_diff_bom = fields.Boolean('Khác định mức?', compute='compute_qty_used_bom')
    qty_used = fields.Float(string='Actual quantity used', digits=dp.get_precision('Product Unit of Measure'),
                            required=True, help="Actual quantity used", default=lambda *a: 1)
    qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
                             compute='compute_available_qty_supply')
    qty_in_loc = fields.Float(string='Số lượng tại tủ', required=True, help="Số lượng khả dụng trong tủ trực",
                              compute='compute_available_qty_supply_in_location')
    is_warning_location = fields.Boolean('Cảnh báo tại tủ', compute='compute_available_qty_supply_in_location')
    location_id = fields.Many2one('stock.location', 'Stock location', domain="[('usage', '=', 'internal')]")
    medicament_type = fields.Selection(MEDICAMENT_TYPE, related="supply.medicament_type", string='Medicament Type',
                                       store=True)

    services = fields.Many2many('sh.medical.health.center.service', 'sh_surgery_specialty_service_rel',
                                track_visibility='onchange',
                                string='Dịch vụ thực hiện')
    service_related = fields.Many2many('sh.medical.health.center.service', 'sh_surgery_specialty_service_related_rel',
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
                # TODO xử lý code chạy cho nhanh bằng cách không check số lượng tự động mà bấm nút check
                #  số lương khi cần
                record.qty_avail = record.uom_id._compute_quantity(record.supply.qty_available,
                                                                   record.supply.uom_id) if record.uom_id != record.supply.uom_id else record.supply.qty_available
            else:
                record.qty_avail = 0

    @api.depends('supply', 'location_id', 'qty_used', 'uom_id')
    def compute_available_qty_supply_in_location(self):  # so luong kha dung tai tu
        for record in self:
            if record.supply:
                # TODO xử lý code chạy cho nhanh bằng cách không check số lượng tự động mà bấm nút check
                #  số lương khi cần
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

    # @api.depends('location_id')
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = record.name
    #         if self.env.context.get('show_short_name'):
    #             name =
    #         result.append((record.id, name))
    #     return result

    @api.onchange('supply')
    def _change_product_id(self):
        self.uom_id = self.supply.uom_id
        self.services = self.name.services

        domain = {'domain': {'uom_id': [('category_id', '=', self.supply.uom_id.category_id.id)]}}
        if self.medicament_type == 'Medicine':
            self.location_id = self.name.perform_room.location_medicine_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'medicine'),
                                               ('company_id', '=', self.name.institution.his_company.id)]
        elif self.medicament_type == 'Supplies':
            self.location_id = self.name.perform_room.location_supply_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'supply'),
                                               ('company_id', '=', self.name.institution.his_company.id)]
        return domain

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.supply.uom_id.category_id:
            self.uom_id = self.supply.uom_id
            raise Warning(
                _('The Supply Unit of Measure and the Material Unit of Measure must be in the same category.'))


class SHealthSpecialty(models.Model):
    _name = "sh.medical.specialty"
    _description = "Services in specialty Management"
    _order = "walkin"
    _inherit = ['mail.thread']

    # STATES = [
    #     ('Draft', 'Draft'),
    #     ('Confirmed', 'Confirmed'),
    #     ('In Progress', 'In Progress'),
    #     ('Done', 'Done'),
    #     ('Cancelled', 'Cancelled'),
    # ]

    GENDER = [
        ('Male', 'Male'),
        ('Female', 'Female')
    ]

    # WARD_TYPE = [
    #     ('Examination', 'Examination'),
    #     ('Laboratory', 'Laboratory'),
    #     ('Imaging', 'Imaging'),
    #     ('Surgery', 'Surgery'),
    #     ('Inpatient', 'Inpatient'),
    #     ('Spa', 'Spa'),
    #     ('Laser', 'Laser'),
    #     ('Odontology', 'Odontology')
    # ]

    REGION = [
        ('North', 'Miền Bắc'),
        ('South', 'Miền Nam')
    ]

    def _get_physician(self):
        """Return default physician value"""
        user_ids = self.env['sh.medical.physician'].search([('sh_user_id', '=', self.env.uid)])
        if user_ids:
            return user_ids.id or False
        else:
            return False

    def _patient_age_at_specialty(self):
        def compute_age_from_dates(patient_dob, patient_services_date):
            if patient_dob and patient_services_date:
                dob = datetime.datetime.strptime(patient_dob.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
                services_date = datetime.datetime.strptime(patient_services_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                           '%Y-%m-%d %H:%M:%S').date()
                delta = services_date - dob
                # years_months_days = _(str(delta.days // 365) + " years " + str(delta.days % 365) + " days")
                # years_months_days = _("%s tuổi %s ngày"%(str(delta.days // 365),str(delta.days%365)))
                years_months_days = _("%s tuổi" % (str(delta.days // 365)))
            else:
                years_months_days = _("No DoB !")
            return years_months_days

        result = {}
        for patient_data in self:
            patient_data.computed_age = compute_age_from_dates(patient_data.patient.birth_date,
                                                               patient_data.services_date)
        return result

    def _specialty_duration(self):
        for sp in self:
            if sp.services_end_date and sp.services_date:
                services_date = 1.0 * calendar.timegm(
                    time.strptime(sp.services_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))
                services_end_date = 1.0 * calendar.timegm(
                    time.strptime(sp.services_end_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))
                duration = (services_end_date - services_date) / 3600
                sp.services_length = duration
            else:
                sp.services_length = 0
        return True

    def get_domain_physician(self):
        # Fix id để truy xuất nhanh hơn
        # shealth_all_in_one.11  => 2
        # shealth_all_in_one.51  => 8
        return [('is_pharmacist', '=', False), ('speciality', 'in', [2, 8])]
        # if self.env.ref('shealth_all_in_one.11', False) and self.env.ref('shealth_all_in_one.51', False):
        #     return [('is_pharmacist', '=', False), (
        #         'speciality', 'in',
        #         [self.env.ref('shealth_all_in_one.11').id, self.env.ref('shealth_all_in_one.51').id])]
        # elif self.env.ref('shealth_all_in_one.11', False):
        #     return [('is_pharmacist', '=', False), ('speciality', 'in', [self.env.ref('shealth_all_in_one.11').id])]
        # elif self.env.ref('shealth_all_in_one.51', False):
        #     return [('is_pharmacist', '=', False), ('speciality', 'in', [self.env.ref('shealth_all_in_one.51').id])]
        # else:
        #     return [('is_pharmacist', '=', False)]

    def get_domain_department(self):
        if self.env.context.get('department_type'):
            return [('company_id', '=', self.env.company.id),
                    ('type', 'in', [self.env.context.get('department_type'), 'Surgery'])]
        else:
            return [('company_id', '=', self.env.company.id), ('type', 'in', ['Spa', 'Laser', 'Odontology'])]

        # institution = self.env['sh.medical.health.center'].search([('his_company', '=', self.env.company.id)], limit=1)
        # if self.env.context.get('department_type'):
        #     return [('institution', '=', self.env.company.id),
        #             ('type', 'in', [self.env.context.get('department_type'), 'Surgery'])]
        # else:
        #     return [('institution', '=', self.env.company.id), ('type', 'in', ['Spa', 'Laser', 'Odontology'])]

    name = fields.Char(string='Specialty #', size=64, readonly=True, required=True, default=lambda *a: '/')
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True,
                              states={'Draft': [('readonly', False)]})
    pathology = fields.Many2one('sh.medical.pathology', string='Condition', help="Base Condition / Reason",
                                readonly=True, states={'Draft': [('readonly', False)]})
    services = fields.Many2many('sh.medical.health.center.service', 'sh_specialty_service_rel', 'specialty_id',
                                'service_id',
                                domain="[('service_department', '=', department)]", readonly=False,
                                states={'Completed': [('readonly', True)]}, track_visibility='onchange',
                                string='Services')
    computed_age = fields.Char(compute=_patient_age_at_specialty, size=32, string='Age during services',
                               help="Computed patient age at the moment of the services", readonly=True,
                               states={'Draft': [('readonly', False)]})
    gender = fields.Selection(GENDER, string='Gender', readonly=True, states={'Draft': [('readonly', False)]})
    physician = fields.Many2one('sh.medical.physician', string='Physician', help="Physician who did the procedure",
                                # domain=lambda self:self.get_domain_physician(),
                                readonly=False, states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
                                default=_get_physician)
    sub_physician = fields.Many2one('sh.medical.physician', string='Trợ thủ/Điều dưỡng phụ', readonly=False,
                                    states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
                                    default=_get_physician)
    date_requested = fields.Datetime(string='Ngày giờ chỉ định', help="Ngày giờ chỉ định", readonly=False,
                                     states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
                                     default=lambda *a: datetime.datetime.now())
    services_date = fields.Datetime(string='Start date & time', help="Start of the Services", readonly=False,
                                    states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]},
                                    default=lambda *a: datetime.datetime.now())
    services_end_date = fields.Datetime(string='End date & time', help="End of the Services", readonly=False,
                                        states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    services_length = fields.Float(compute=_specialty_duration, string='Duration (Hour:Minute)',
                                   help="Length of the services", readonly=True,
                                   states={'Draft': [('readonly', False)]})
    description = fields.Text(string='Description', readonly=True,
                              states={'Draft': [('readonly', False)], 'Confirmed': [('readonly', False)],
                                      'In Progress': [('readonly', False)]})
    info = fields.Text(string='Extra Info', readonly=True,
                       states={'Draft': [('readonly', False)], 'Confirmed': [('readonly', False)],
                               'In Progress': [('readonly', False)]})
    institution = fields.Many2one('sh.medical.health.center',
                                  string='Health Center',
                                  help="Health Center",
                                  required=True, readonly=False,
                                  states={'Done': [('readonly', True)],
                                          'Signed': [('readonly', True)]})
    company_id = fields.Many2one('res.company', related='institution.his_company', string='Company', store=True,
                                 readonly=True)
    specialty_team = fields.One2many('sh.medical.specialty.team', 'name', string='Team Members',
                                     help="Professionals Involved in the surgery", readonly=False,
                                     states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    supplies = fields.One2many('sh.medical.specialty.supply', 'name', string='Supplies',
                               help="List of the supplies required for the services", readonly=False,
                               states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    department = fields.Many2one('sh.medical.health.center.ward', string='Department',
                                 domain=lambda self: self.get_domain_department(),
                                 help="Department of the selected Health Center", required=True, readonly=False,
                                 states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    department_type = fields.Selection(related="department.type", store=True, depends=['department'])

    perform_room = fields.Many2one('sh.medical.health.center.ot', string='Performance room',
                                   domain="[('department','=',department)]", readonly=False,
                                   states={'Done': [('readonly', True)], 'Signed': [('readonly', True)]})
    state = fields.Selection([('Draft', 'Draft'),
                              ('Confirmed', 'Confirmed'),
                              ('In Progress', 'In Progress'),
                              ('Done', 'Done'),
                              ('Cancelled', 'Cancelled')],
                             readonly=True,
                             default='Draft')

    other_bom = fields.Many2many('sh.medical.product.bundle', 'sh_specialty_bom_rel', 'specialty_id', 'bom_id',
                                 string='All BOM of service',
                                 domain="[('service_id', 'in', services),('region', '=', region),('type', '=', 'Specialty')]")

    #  check công ty hiện tại của người dùng với công ty của phiếu
    check_current_company = fields.Boolean(string='Cty hiện tại', compute='_check_current_company')

    #  domain vật tư và thuốc theo kho của phòng
    supply_domain = fields.Many2many('sh.medical.medicines', string='Supply domain', compute='_get_supply_domain')

    uom_price = fields.Integer(string='Số lượng thực hiện',
                               help="Răng/cm2/...", default=1, compute="_get_uom_price()", store=True)

    show_specialty = fields.Boolean(string='Check chuyên khoa?', compute='_check_specialty')

    # trường ghi nhận phiếu được chỉ định thêm ngoài cấu hình
    is_new_request = fields.Boolean(string='Là chỉ định thêm', help="Phiếu được chỉ định thêm", default=False)

    # vùng miền
    region = fields.Selection(REGION, string='Miền', help="Vùng miền", related="institution.region")

    # Phiếu khám
    walkin = fields.Many2one('sh.medical.appointment.register.walkin',
                             string='Queue #',
                             required=True,
                             readonly=True,
                             ondelete='cascade')

    services_domain = fields.Many2many('sh.medical.health.center.service',
                                       related='walkin.service',
                                       string="Services Domain")

    allow_institutions = fields.Many2many('sh.medical.health.center',
                                          string='Allow institutions',
                                          related='walkin.allow_institutions')

    booking_id = fields.Many2one('crm.lead', related='walkin.booking_id', store=True)
    code_booking = fields.Char(string='Mã booking tương ứng', related='booking_id.name', store=True)

    reason_check = fields.Text(string="Lý do khám", related='walkin.reason_check')

    teeths = fields.Many2many('sh.medical.teeth', 'sh_specialty_teeth_related_rel', 'specialty_id', 'teeth_id',
                              string='Mã răng',
                              store=True,
                              compute="_get_teeths_specialty")

    # Áp dụng rule Phiếu PTTT - share company
    booking_company_id = fields.Many2one('res.company', related='booking_id.company_id',
                                         string='Company',
                                         store=True,
                                         readonly=True,
                                         ondelete='cascade')
    booking_company2_id = fields.Many2many('res.company', 'sh_medial_specialty_company_related_rel', 'surgery_id',
                                           'company_id',
                                           related='booking_id.company2_id',
                                           store=True,
                                           readonly=True,
                                           ondelete='cascade')

    @api.onchange('walkin')
    def get_service(self):
        self.services = False
        if self.walkin:
            self.services = [(6, 0, self.walkin.service.filtered(lambda s: not s.is_no_specialty).ids)]

    @api.depends('services')
    def _get_teeths_specialty(self):
        for rec in self:
            if rec.services:
                so_line_teeth = rec.walkin.sale_order_id.order_line
                if so_line_teeth:
                    rec.teeths = so_line_teeth.filtered(
                        lambda s: s.product_id.id in rec.services.mapped('product_id').ids).mapped('teeth_ids')
                else:
                    rec.teeths = False
            else:
                rec.teeths = False

    @api.depends('teeths')
    def _get_uom_price(self):
        for record in self.with_env(self.env(su=True)):
            if record.teeths:
                record.uom_price = len(record.teeths)
            else:
                record.uom_price = 1

    @api.depends('department')
    def _check_specialty(self):
        for record in self.with_env(self.env(su=True)):
            record.show_specialty = False

            # check quyền để hiện nút xem chi tiết phiếu
            if self.env.user.has_group(
                    'shealth_all_in_one.group_sh_medical_physician_spa') and record.department.type == 'Spa':
                record.show_specialty = True
            elif self.env.user.has_group(
                    'shealth_all_in_one.group_sh_medical_physician_laser') and record.department.type == 'Laser':
                record.show_specialty = True
            elif self.env.user.has_group(
                    'shealth_all_in_one.group_sh_medical_physician_odontology') and record.department.type == 'Odontology':
                record.show_specialty = True

    @api.onchange('uom_price')
    def onchange_uom_price(self):
        if self.department and self.department.type == 'Odontology':
            if self.uom_price < 0:
                raise ValidationError(_('Số lượng phải > 0'))

            if self.uom_price > self.walkin.uom_price:
                raise ValidationError(_('Số lượng phải ít hơn số lượng từ Phiếu khám.'))

            self.supplies = False

    # cộng dồn số lượng vật tư nếu đã nhập rồi
    @api.onchange('supplies')
    def _onchange_supplies(self):
        if self.supplies:
            id_supplies = {}
            inx = 0
            for supply in self.supplies:
                if str(supply.supply.id) in id_supplies:
                    # print('đã có: cộng dồn số lượng')
                    qty_sup = self.supplies[id_supplies[str(supply.supply.id)]].qty_used + supply.qty_used
                    self.supplies[id_supplies[str(supply.supply.id)]].qty_used = qty_sup
                    self.supplies = [(2, supply.id, False)]
                else:
                    id_supplies[str(supply.supply.id)] = inx
                    # print('chưa có')
                inx += 1

    @api.depends('company_id')
    def _check_current_company(self):
        for record in self:
            record.check_current_company = True if record.company_id == self.env.company else False

    @api.depends('perform_room')
    def _get_supply_domain(self):
        for record in self:
            # Với trạng thái Confirmed và In Progress thì hiển thị tính toán
            # Trạng thái Draft chưa cần tính toán
            # Trạng thái Done ?
            record.supply_domain = False
            if record.state in ['Confirmed', 'In Progress']:

                room = record.perform_room
                if room:
                    locations = room.location_medicine_stock + room.location_supply_stock
                    if locations:
                        stock_quants = self.env['stock.quant'].search([('quantity', '>', 0),
                                                                       ('location_id', 'in', locations.ids)])
                        products = stock_quants.filtered(lambda q: q.reserved_quantity < q.quantity).mapped(
                            'product_id')
                        if products:
                            medicines = self.env['sh.medical.medicines'].search([('product_id', 'in', products.ids)])
                            record.supply_domain = [(6, 0, medicines.ids)]

    @api.onchange('date_requested', 'services_date', 'services_end_date')
    def _onchange_date_specialty(self):
        if self.services_date and self.date_requested and self.services_end_date:
            if self.services_date < self.date_requested or self.services_date > self.services_end_date:
                raise UserError(
                    _(
                        'Thông tin không hợp lệ! Ngày giờ thực hiện phải sau ngày giờ chỉ định và trước ngày kết thúc!'))

    def write(self, vals):
        res = super(SHealthSpecialty, self).write(vals)

        for record in self.with_env(self.env(su=True)):
            # CASE ĐỔI CHI NHÁNH THỰC HIỆN: Cập nhật lại công ty ở SO để ghi nhận doanh thu cho cơ sở thự hiện
            if vals.get('institution'):
                institution_detail = self.env['sh.medical.health.center'].browse(vals.get('institution'))

                # lấy kho của công ty
                ins_warehouse = self.env['stock.warehouse'].with_env(self.env(su=True)).search(
                    [('company_id', '=', institution_detail.his_company.id)], limit=1)
                if not ins_warehouse:
                    raise ValidationError(_('Công ty bạn chọn không có kho hàng!'))

                record.walkin.sale_order_id.write(
                    {'company_id': institution_detail.his_company.id, 'warehouse_id': ins_warehouse.id})

            if vals.get('date_requested') or vals.get('services_date') or vals.get('services_end_date'):
                date_requested = vals.get('date_requested') or record.date_requested
                services_date = vals.get('services_date') or record.services_date
                services_end_date = vals.get('services_end_date') or record.services_end_date

                # format to date
                if isinstance(date_requested, str):
                    date_requested = datetime.datetime.strptime(date_requested, '%Y-%m-%d %H:%M:%S')
                if isinstance(services_date, str):
                    services_date = datetime.datetime.strptime(services_date, '%Y-%m-%d %H:%M:%S')
                if isinstance(services_end_date, str):
                    services_end_date = datetime.datetime.strptime(services_end_date, '%Y-%m-%d %H:%M:%S')

                if services_date and date_requested and services_end_date and (
                        services_date < date_requested or services_date > services_end_date):
                    raise UserError(
                        _(
                            'Thông tin không hợp lệ! Ngày giờ thực hiện phải sau ngày giờ chỉ định và trước ngày kết thúc!'))

            if vals.get('services'):
                # check dịch vụ đổi trong phiếu chuyên khoa: nếu xóa sẽ xóa dv sẽ xóa ở dv ở thành viên tham gia
                # thành viên tham gia
                for specialty_mem in record.specialty_team.mapped('service_performances').ids:
                    if specialty_mem not in record.services.ids:
                        record.specialty_team.write({'service_performances': [(3, specialty_mem)]})

                # vtth
                for specialty_sur in record.supplies.mapped('services').ids:
                    if specialty_sur not in record.services.ids:
                        record.supplies.write({'services': [(3, specialty_sur)]})

            if vals.get('supplies') and record.state == 'Done':
                raise ValidationError('Bạn không thể chỉnh sửa khi đã kết thúc phiếu')

        return res

    def view_detail_specialty(self):
        return {
            'name': _('Chi tiết Chuyên khoa'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_specialty_view').id,
            'res_model': 'sh.medical.specialty',  # model want to display
            'target': 'current',  # if you want popup,
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': self.id
        }

    @api.onchange('perform_room', 'other_bom')
    def _onchange_other_bom(self):
        self.supplies = False
        if self.other_bom:
            vals = []
            check_duplicate = []
            for record in self.other_bom:
                for record_line in record.products.filtered(lambda p: p.note == 'Specialty'):
                    location = self.perform_room.location_supply_stock
                    if record_line.product_id.medicament_type == 'Medicine':
                        location = self.perform_room.location_medicine_stock
                    # product = record_line.product_id.product_id  # product.product
                    if location:
                        # available_qty = self.env['stock.quant']._get_available_quantity(product_id=product, location_id=location)
                        # if record_line.uom_id != product.uom_id:
                        #     available_qty = product.uom_id._compute_quantity(available_qty, record_line.uom_id)

                        uom_price = self.uom_price if self.department and self.department.type == 'Odontology' else 1

                        # qty = min(record_line.quantity * uom_price, available_qty)
                        qty = record_line.quantity * uom_price
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

        # Tự động chọn BOM theo dịch vụ (Phiếu PTTT)
        @api.onchange('services')
        def get_default_other_bom(self):
            self.other_bom = False
            if self.services:
                list_result = []
                for service in self.services:
                    other_bom = self.env['sh.medical.product.bundle'].search(
                        [('service_id', '=', service._origin.id), ('type', '=', 'Surgery'),
                         ('region', '=', self.region)],
                        limit=1)
                    if other_bom:
                        list_result.append(other_bom.id)
                self.other_bom = [(6, 0, list_result)]

    @api.onchange('institution')
    def _onchange_institution(self):
        # set khoa mac dinh la chuyen khoa cua co so y te
        if self.institution:
            specialty_dep = self.env['sh.medical.health.center.ward'].search(
                [('institution', '=', self.institution.id), ('type', '=', 'Specialty')], limit=1)
            self.department = specialty_dep
            self.perform_room = False

    @api.onchange('department')
    def _onchange_department(self):
        if self.department:
            self.perform_room = False

    @api.model
    def create(self, vals):
        specialty_dep = self.env['sh.medical.health.center.ward'].search(
            [('id', '=', vals['department'])])
        # print(specialty_dep.type)
        sequence = self.env['ir.sequence'].next_by_code(
            'sh.medical.specialty.%s.%s' % (specialty_dep.type, vals['institution']))
        if not sequence:
            raise ValidationError(_('Định danh phiếu Chuyên khoa của Cơ sở y tế này đang không tồn tại!'))
        vals['name'] = sequence
        # print(sequence)
        return super(SHealthSpecialty, self).create(vals)

    def action_specialty_confirm(self):
        if self.sudo().walkin.state == 'WaitPayment':
            raise ValidationError(
                _('Bạn không thể xác nhận phiếu do Phiếu Khám liên quan của phiếu này chưa thu đủ tiền làm dịch vụ!'))

        # Tự động chọn BOM theo dịch vụ
        if self.services:
            list_result = []
            for service in self.services:
                other_bom = self.env['sh.medical.product.bundle'].search(
                    [('service_id', '=', service._origin.id), ('type', '=', 'Specialty'),
                     ('region', '=', self.region)],
                    limit=1)
                if other_bom:
                    list_result.append(other_bom.id)
            self.other_bom = [(6, 0, list_result)]
            self._onchange_other_bom()

        # nếu chưa nhập vtth thì đổ bom theo cấu hình
        if not self.supplies:
            # add vat tu tieu hao ban dau cho chuyen khoa
            sg_data = []
            check_duplicate = []
            # self.supplies = False #NÊN GIỮ LẠI VTTH ĐÃ NHẬP

            for ser in self.services:
                # add vat tu tieu hao tong - ban dau
                for mats in ser.material_ids.filtered(lambda m: m.note == 'Specialty'):
                    # print(mats)
                    location = self.perform_room.location_supply_stock
                    if mats.product_id.medicament_type == 'Medicine':
                        location = self.perform_room.location_medicine_stock
                    product = mats.product_id.product_id  # product.product
                    if location:
                        available_qty = self.env['stock.quant']._get_available_quantity(product_id=product,
                                                                                        location_id=location)
                        if mats.uom_id != product.uom_id:
                            available_qty = product.uom_id._compute_quantity(available_qty, mats.uom_id)

                        uom_price = self.uom_price if self.department and self.department.type == 'Odontology' else 1
                        qty = min(mats.quantity * uom_price, available_qty)

                        # if qty > 0:
                        mats_id = mats.product_id.id
                        if mats_id not in check_duplicate:
                            check_duplicate.append(mats_id)
                            sg_data.append((0, 0, {'supply': mats_id,
                                                   'qty': mats.quantity * uom_price,
                                                   'qty_used': qty,
                                                   'uom_id': mats.uom_id.id,
                                                   'location_id': location.id,
                                                   'services': [(4, ser.id)],
                                                   'notes': mats.note}))
                        else:
                            old_supply_index = check_duplicate.index(mats_id)
                            sg_data[old_supply_index][2]['services'] += [(4, ser.id)],
                            sg_data[old_supply_index][2]['qty'] += mats.quantity * uom_price
                            sg_data[old_supply_index][2]['qty_used'] = min(
                                qty + sg_data[old_supply_index][2]['qty_used'], available_qty)

            # ghi nhận ngày làm dịch vụ là ngày bấm xác nhận phiếu
            self.write({'state': 'Confirmed', 'supplies': sg_data, 'services_date': fields.Datetime.now(),
                        'services_end_date': fields.Datetime.now() + timedelta(hours=2)})
        else:
            self.write({'state': 'Confirmed'})

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

    def action_specialty_start(self):
        if self.state == 'Done':
            self.reverse_materials()
            self.sudo().walkin.update_walkin_material(mats_types=['Specialty'])
            res = self.write({'state': 'In Progress'})
        else:
            if self.services_date:
                services_date = self.services_date
            else:
                services_date = datetime.datetime.now()
            res = self.write({'state': 'In Progress', 'services_date': services_date})
        # return res

    def action_cancelled(self):
        if self.state != 'Draft':
            raise ValidationError('Bạn chỉ có thể hủy khi phiếu ở trạng thái NHÁP')
        else:
            self.state = 'Cancelled'

    def action_specialty_set_to_draft(self):
        self.other_bom = False
        self.supplies = False
        self.write({'state': 'Draft'})

    def action_specialty_end(self):
        self.ensure_one()
        services_end_date = self.services_end_date if self.services_end_date else datetime.datetime.now()
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

                # TU DONG XÁC NHẬN XUAT KHO
                stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
                for move_line in stock_picking.move_ids_without_package:
                    for move_live_detail in move_line.move_line_ids:
                        move_live_detail.qty_done = move_live_detail.product_uom_qty
                    # move_line.quantity_done = move_line.product_uom_qty
                stock_picking.with_context(
                    force_period_date=services_end_date).sudo().button_validate()  # ham tru product trong inventory, sudo để đọc stock.valuation.layer

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

    def unlink(self):
        for specialty in self.filtered(lambda sp: sp.state not in ['Draft']):
            # raise UserError(_('You can not delete a record that is not in Draft !!'))
            raise UserError(_('Bạn không thể xóa Phiếu Chuyên khoa khi phiếu đang không ở trạng thái Nháp!'))
        return super(SHealthSpecialty, self).unlink()

    def reset_all_supply(self):
        for specialty in self.filtered(lambda sp: sp.state not in ['Draft', 'Done']):
            specialty.supplies = False
