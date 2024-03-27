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

import datetime
from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError


# Patient Roundings Management

class SHealthPatientRoundingProcedures(models.Model):
    _name = 'sh.medical.patient.rounding.procedure'
    _description = 'Patient Procedures For Roundings'

    name = fields.Many2one('sh.medical.patient.rounding', string='Rouding')
    procedures = fields.Many2one('sh.medical.procedure', string='Procedures', required=True)
    notes = fields.Text('Notes')


class SHealthPatientRoundingMedicines(models.Model):
    _name = 'sh.medical.patient.rounding.medicines'
    _description = 'Patient Medicines For Roundings'

    MEDICAMENT_TYPE = [
        ('Medicine', 'Medicine'),
        ('Supplies', 'Supplies'),
        ('CCDC', 'CCDC')
    ]

    name = fields.Many2one('sh.medical.patient.rounding', string='Rounding')
    # medicine = fields.Many2one('sh.medical.medicines', string='Medicines and Supply', domain=lambda self:[('categ_id','child_of',self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)], required=True)
    medicine = fields.Many2one('sh.medical.medicines', string='Medicines and Supply', required=True)
    # medicine = fields.Many2one('sh.medical.medicines', string='Medicines', domain=[('medicament_type','=','Medicine')], required=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    init_qty = fields.Float(string='Initial required quantity', digits='Product Unit of Measure', required=True,
                       help="Initial required quantity", default=lambda *a: 0)
    qty = fields.Float("Quantity", digits='Product Unit of Measure',default=lambda *a: 1)
    qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
                             compute='compute_available_qty_supply')
    qty_in_loc = fields.Float(string='Số lượng tại tủ', required=True, help="Số lượng khả dụng trong tủ trực",
                              compute='compute_available_qty_supply_in_location')
    is_warning_location = fields.Boolean('Cảnh báo tại tủ', compute='compute_available_qty_supply_in_location')

    notes = fields.Text('Comment')

    location_id = fields.Many2one('stock.location', 'Stock location', domain="[('usage', '=', 'internal')]")
    medicament_type = fields.Selection(MEDICAMENT_TYPE, related="medicine.medicament_type", string='Medicament Type',
                                       store=True)

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự

    services = fields.Many2many('sh.medical.health.center.service', 'sh_rounding_medicines_service_rel', string='Dịch vụ thực hiện')
    service_related = fields.Many2many('sh.medical.health.center.service', 'sh_rounding_medicines_service_related_rel', related="name.services",
                               string='Dịch vụ liên quan')

    indications = fields.Many2one('sh.medical.drug.route', string="Đường dùng", help="Đường dùng của thuốc")
    dosage = fields.Text('Liều dùng')

    picking_id = fields.Many2one('stock.picking', string='Phiếu điều chuyển')

    @api.depends('medicine', 'uom_id')
    def compute_available_qty_supply(self):  # so luong kha dung toan vien
        for record in self:
            if record.medicine:
                record.qty_avail = record.uom_id._compute_quantity(record.medicine.qty_available,
                                                                   record.medicine.uom_id) if record.uom_id != record.medicine.uom_id else record.medicine.qty_available
            else:
                record.qty_avail = 0

    @api.depends('medicine', 'location_id', 'qty', 'uom_id')
    def compute_available_qty_supply_in_location(self):  # so luong kha dung tai tu
        for record in self:
            if record.medicine:
                quantity_on_hand = self.env['stock.quant'].with_user(1)._get_available_quantity(
                    record.medicine.product_id,
                    record.location_id)  # check quantity trong location

                record.qty_in_loc = record.uom_id._compute_quantity(quantity_on_hand,
                                                                    record.medicine.uom_id) if record.uom_id != record.medicine.uom_id else quantity_on_hand
            else:
                record.qty_in_loc = 0

            record.is_warning_location = True if record.qty > record.qty_in_loc else False

    @api.onchange('qty', 'medicine')
    def onchange_qty(self):
        if self.qty < 0 and self.medicine:
            raise UserError(_("Số lượng nhập phải lớn hơn 0!"))

    @api.onchange('medicine')
    def _change_product_id(self):
        domain = {'domain': {'uom_id': [('category_id', '=', self.medicine.uom_id.category_id.id)]}}
        institution = self.name.inpatient_id.institution
        room = self.name.inpatient_id.bed.room
        self.uom_id = self.medicine.uom_id
        self.indications = self.medicine.indications
        self.dosage = self.medicine.dosage

        if self.medicament_type == 'Medicine':
            self.location_id = room.location_medicine_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'medicine'), ('company_id', '=', institution.his_company.id)]
        elif self.medicament_type == 'Supplies':
            self.location_id = room.location_supply_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'supply'), ('company_id', '=', institution.his_company.id)]
        return domain


class SHealthRoundingTeam(models.Model):
    _name = "sh.medical.rounding.team"
    _description = "Rounding Team"

    # _sql_constraints = [('name_unique', 'unique(name,team_member,role,service_performances)',
    #                      "Vai trò của thành viên phải là duy nhất!")]

    def get_domain_role(self):
        if self.env.context.get('department_type'):
            return [('type','=', self.env.context.get('department_type').lower())]
        else:
            return [('type','=', 'surgery')]

    @api.constrains('name', 'team_member', 'service_performances', 'role')
    def _check_constrains_team_member(self):
        for rec in self:
            similars = self.env['sh.medical.rounding.team'].search(
                [('id','!=',rec.id), ('name', '=', rec.name.id), ('team_member', '=', rec.team_member.id), ('role', '=', rec.role.id)])
            if similars:
                for sim_rec in similars:
                    for rec_service in rec.service_performances:
                        if rec_service in sim_rec.service_performances:
                            raise ValidationError('Vai trò của thành viên với dịch vụ phải là duy nhất!')

    name = fields.Many2one('sh.medical.patient.rounding', string='Phiếu CSHP')
    team_member = fields.Many2one('sh.medical.physician', string='Thành viên',
                                  help="Health professional that participated on this surgery",
                                  domain=[('is_pharmacist', '=', False)], required=True)

    service_performances = fields.Many2many('sh.medical.health.center.service', 'sh_rounding_team_services_rel',
                                            'rounding_team_id', 'service_id', string='Dịch vụ thực hiện',
                                            help="Các dịch vụ của thành viên với vai trò này thực hiện")

    role = fields.Many2one('sh.medical.team.role', string='Vai trò', domain=lambda self:self.get_domain_role())
    notes = fields.Char(string='Note')


class SHealthPatientRoundingManagement(models.Model):
    _name = 'sh.medical.patient.rounding'
    _description = 'Patient Rounding Management'
    _inherit = ['mail.thread']

    _order = "name"

    STATUS = [
        ('Draft', 'Nháp'),
        ('Completed', 'Hoàn thành'),
        ('cancel', 'Hủy'),
    ]

    EVOLUTION = [
        ('Status Quo', 'Hiện trạng'),
        ('Improving', 'Tiến triển'),
        ('Worsening', 'Xấu đi'),
    ]

    REGION = [
        ('North', 'Miền Bắc'),
        ('South', 'Miền Nam')
    ]

    def _get_patient_rounding(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    def get_nurse(self):
        if self.env.ref('shealth_all_in_one.33',False):
            return [('is_pharmacist', '=', False), ('speciality', '=', self.env.ref('shealth_all_in_one.33').id)]
        else:
            return [('is_pharmacist', '=', False)]

    def get_anesthetist(self):
        if self.env.ref('shealth_all_in_one.5',False):
            return [('is_pharmacist', '=', False), '|' ,('speciality', '=', self.env.ref('shealth_all_in_one.5').id), ('speciality', '=', self.env.ref('shealth_all_in_one.45').id)]
        else:
            return [('is_pharmacist', '=', False)]

    def _get_default_medicines(self):
        # nếu có tồn tại context chứa dịch vụ đã thực hiện
        if self.env.context.get('services_done') and self.env.context.get('room'):
            services = self.env.context.get('services_done')

            UOM = self.env['uom.uom']
            service_materials = self.env['sh.medical.service.material']
            inpatient_room = self.env['sh.medical.health.center.ot']

            domain = [('service_id', 'in', services[0][2]), ('note', '=', 'Inpatient')]
            service_materials_data = service_materials.search(domain)
            inpatient_room_data = inpatient_room.browse(self.env.context.get('room'))

            # ghi nhận vtth nếu có
            materials_rounding = []
            seq = 0

            id_product_material_rounding = []
            for material in service_materials_data:
                #nếu ko có sẽ add thêm vtth đó vào, ko thì bỏ qua
                if material.product_id.id not in id_product_material_rounding:
                    seq += 1

                    if material.product_id.medicament_type == 'Medicine':
                        location_id = inpatient_room_data.location_medicine_stock.id
                    else:
                        location_id = inpatient_room_data.location_supply_stock.id

                    materials_rounding.append((0, 0, {'sequence': seq,
                                                      'location_id': location_id or False,
                                                      'medicine': material.product_id.id,
                                                      'qty': material.quantity,
                                                      'notes': '',
                                                      'services': [(4,material.service_id.id)],
                                                      'uom_id': material.uom_id.id}))

                    id_product_material_rounding.append(material.product_id.id)
                else:  # có rồi thì cộng vào dòng cũ
                    old_mats_index = id_product_material_rounding.index(material.product_id.id)
                    old_uom_id = materials_rounding[old_mats_index][2]['uom_id']
                    # quy đổi sản phẩm nếu đơn vị khác nhau
                    materials_rounding[old_mats_index][2]['qty'] += (material.quantity if old_uom_id == material.uom_id.id else
                                                                     material.uom_id._compute_quantity(material.quantity, UOM.browse(old_uom_id)))
                    materials_rounding[old_mats_index][2]['services'] += [(4, material.service_id.id)]

            return materials_rounding
        else:
            return False

    name = fields.Char(string='Rounding #', size=128, readonly=True, default=lambda *a: '/')
    inpatient_id = fields.Many2one('sh.medical.inpatient', string='Registration Code', required=True, readonly=True, states={'Draft': [('readonly', False)]}, ondelete="cascade")
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True, states={'Draft': [('readonly', False)]})
    doctor = fields.Many2one('sh.medical.physician', domain=lambda self: self.get_anesthetist(),
                             string='Bác sĩ', help="Physician Name", required=True, readonly=True,states={'Draft': [('readonly', False)]}, default=_get_patient_rounding)
    physician = fields.Many2one('sh.medical.physician', domain=lambda self: self.get_nurse(),
                                string='Điều dưỡng viên', help="Physician Name", required=True, readonly=True,states={'Draft': [('readonly', False)]}, default=_get_patient_rounding)
    evaluation_start_date = fields.Datetime(string='Start date & time', required=True, readonly=True, states={'Draft': [('readonly', False)]}, default=lambda *a: datetime.datetime.now())
    evaluation_end_date = fields.Datetime(string='End date & time', readonly=True, states={'Draft': [('readonly', False)]})
    temperature = fields.Float(string='Temperature', help="Temperature in celsius", readonly=True,
                               states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.temperature", store=True)
    bpm = fields.Integer(string='Heart Rate', help="Heart rate expressed in beats per minute", readonly=True,
                         states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.bpm", store=True)
    respiratory_rate = fields.Integer(string='Respiratory Rate',
                                      help="Respiratory rate expressed in breaths per minute", readonly=True,
                                      states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.respiratory_rate", store=True)
    systolic = fields.Integer(string='Systolic Pressure', readonly=True, states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.systolic", store=True)
    diastolic = fields.Integer(string='Diastolic Pressure', readonly=True, states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.diastolic", store=True)
    osat = fields.Integer(string='Oxygen Saturation', help="Oxygen Saturation(arterial)", readonly=True,
                          states={'Draft': [('readonly', False)]})

    # NOT USE
    environmental_assessment = fields.Char('Environment', help="Environment assessment. State any disorder in the room.", size=128, readonly=True, states={'Draft': [('readonly', False)]})
    weight = fields.Integer(string='Weight', help="Measured weight, in kg", readonly=True, states={'Draft': [('readonly', False)]})
    pain = fields.Boolean(string='Pain', help="Check if the patient is in pain", readonly=True, states={'Draft': [('readonly', False)]})
    pain_level = fields.Integer(string='Pain Level (1 to 10)', help="Enter the pain level, from 1 to 10", readonly=True, states={'Draft': [('readonly', False)]})
    potty = fields.Boolean(string='Potty', help="Check if the patient needs to urinate / defecate", readonly=True, states={'Draft': [('readonly', False)]})
    position = fields.Boolean(string='Position', help="Check if the patient needs to be repositioned or is unconfortable", readonly=True, states={'Draft': [('readonly', False)]})
    proximity = fields.Boolean(string='Proximity', help="Check if personal items, water, alarm, ... are not in easy reach", readonly=True, states={'Draft': [('readonly', False)]})
    pump = fields.Boolean(string='Pumps', help="Check if personal items, water, alarm, ... are not in easy reach", readonly=True, states={'Draft': [('readonly', False)]})
    personal_needs = fields.Boolean(string='Personal needs', help="Check if the patient requests anything", readonly=True, states={'Draft': [('readonly', False)]})
    diuresis = fields.Integer(string='Diuresis', help="volume in ml", readonly=True, states={'Draft': [('readonly', False)]})
    urinary_catheter = fields.Integer(string='Urinary Catheter', readonly=True, states={'Draft': [('readonly', False)]})
    glycemia = fields.Integer(string='Glycemia', help="Blood Glucose level", readonly=True, states={'Draft': [('readonly', False)]})
    depression = fields.Boolean(string='Depression Signs', help="Check this if the patient shows signs of depression", readonly=True, states={'Draft': [('readonly', False)]})
    # NOT USE

    evolution = fields.Selection(EVOLUTION, string='Evolution', readonly=True, states={'Draft': [('readonly', False)]})
    round_summary = fields.Text(string="Round Summary", readonly=True, states={'Draft': [('readonly', False)]})
    follow_round_summary = fields.Text(string="Theo dõi diễn biến", readonly=True, states={'Draft': [('readonly', False)]})
    nursing_plan = fields.Text(string='Chế độ dinh dưỡng', readonly=False, states={'Completed': [('readonly', True)]})
    execute = fields.Html(string="Thực hiện y lệnh", readonly=True, states={'Draft': [('readonly', False)]})
    warning = fields.Boolean(string='Warning', help="Check this box to alert the supervisor about this patient rounding. A warning icon will be shown in the rounding list", readonly=True, states={'Draft': [('readonly', False)]})
    procedures = fields.One2many('sh.medical.patient.rounding.procedure', 'name', string='Procedures', help="List of the procedures in this rounding. Please enter the first one as the main procedure", readonly=True, states={'Draft': [('readonly', False)]})
    medicaments = fields.One2many('sh.medical.patient.rounding.medicines', 'name', default=lambda self: self._get_default_medicines(), string='Medicines', help="List of the medicines assigned in this rounding", readonly=True, states={'Draft': [('readonly', False)]})
    state = fields.Selection(STATUS, string='State',readonly=True, default=lambda *a: 'Draft', tracking=True)

    services = fields.Many2many('sh.medical.health.center.service', 'sh_rounding_service_rel', track_visibility='onchange', string='Dịch vụ thực hiện')
    service_related = fields.Many2many('sh.medical.health.center.service', 'sh_rounding_service_related_rel', related="inpatient_id.services",
                                       string='Dịch vụ liên quan')

    other_bom = fields.Many2many('sh.medical.product.bundle', string='All BOM of service', domain="[('service_id', 'in', services),('region', '=', region),('type', '=', 'Inpatient')]")

    #  check công ty hiện tại của người dùng với công ty của phiếu
    check_current_company = fields.Boolean(string='Cty hiện tại', compute='_check_current_company')

    #  domain vật tư và thuốc theo kho của phòng
    supply_domain = fields.Many2many('sh.medical.medicines', string='Supply domain', compute='_get_supply_domain')

    # vùng miền
    region = fields.Selection(REGION, string='Miền', help="Vùng miền", related="inpatient_id.institution.region")

    rounding_team = fields.One2many('sh.medical.rounding.team', 'name', string='Thành viên tham gia',
                                      help="Thành viên tham gia CSHP", readonly=False,
                                      states={'Completed': [('readonly', True)]})

    # trường ghi nhận phiếu được chỉ định thêm
    is_new_request = fields.Boolean(string='Là chỉ định thêm', help="Phiếu được chỉ định thêm", default=False)

    def action_cancelled(self):
        if self.state != 'Draft':
            raise ValidationError('Bạn chỉ có thể hủy khi phiếu ở trạng thái NHÁP')
        else:
            self.state = 'cancel'

    @api.depends('inpatient_id.institution.his_company')
    def _check_current_company(self):
        for record in self:
            record.check_current_company = True if record.inpatient_id.institution.his_company == self.env.company else False

    @api.depends('inpatient_id.room')
    def _get_supply_domain(self):
        for record in self:
            record.supply_domain = False
            room = record.inpatient_id.room
            if room:
                locations = room.location_medicine_stock + room.location_supply_stock
                if locations:
                    products = self.env['stock.quant'].search([('quantity', '>', 0), ('location_id', 'in', locations.ids)]).filtered(lambda q: q.reserved_quantity < q.quantity).mapped('product_id')
                    if products:
                        medicines = self.env['sh.medical.medicines'].search([('product_id', 'in', products.ids)])
                        record.supply_domain = [(6, 0, medicines.ids)]

    @api.onchange('evaluation_start_date')
    def _onchange_date(self):
        # if not self.evaluation_end_date:
        self.evaluation_end_date = self.evaluation_start_date

    @api.onchange('other_bom')
    def _onchange_other_bom(self):
        if self.other_bom:
            self.medicaments = False
            vals = []
            check_duplicate = []
            Room = self.env['sh.medical.health.center.ot']
            for record in self.other_bom:
                for record_line in record.products.filtered(lambda p: p.note == 'Inpatient'):
                    location = self.inpatient_id.room.location_supply_stock or Room.browse(self.env.context.get('room')).location_supply_stock
                    if record_line.product_id.medicament_type == 'Medicine':
                        location = self.inpatient_id.room.location_medicine_stock or Room.browse(self.env.context.get('room')).location_medicine_stock
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
                            vals.append((0, 0, {'medicine': mats_id,
                                                'init_qty': qty,
                                                'qty': qty,
                                                'uom_id': record_line.uom_id.id,
                                                'location_id': location.id,
                                                'indications': record_line.product_id.indications,
                                                'dosage': record_line.product_id.dosage,
                                                'services': [(4, record.service_id.id)],
                                                'notes': record_line.note}))
                        else:
                            old_supply_index = check_duplicate.index(mats_id)
                            vals[old_supply_index][2]['services'] += [(4, record.service_id.id)]
                            vals[old_supply_index][2]['init_qty'] += qty
                            vals[old_supply_index][2]['qty'] += qty

            print(vals)
            self.medicaments = vals
            for medicament in self.medicaments:
                if medicament.uom_id.int_rounding:
                    medicament.qty = round(medicament.qty/len(medicament.services))
                    medicament.init_qty = round(medicament.init_qty/len(medicament.services))
                else:
                    medicament.qty = medicament.qty/len(medicament.services)
                    medicament.init_qty = medicament.init_qty/len(medicament.services)
        elif self._origin:  # chỉ xóa medicaments khi bản ghi đã có inpatient_id, không xóa default medicaments nếu tạo mới
            self.medicaments = False

    # cộng dồn số lượng vật tư nếu đã nhập rồi
    @api.onchange('medicaments')
    def _onchange_medicaments(self):
        if self.medicaments:
            id_medicaments = {}
            inx = 0
            for medicament in self.medicaments:
                if str(medicament.medicine.id) in id_medicaments:
                    # print('đã có: cộng dồn số lượng')
                    qty_sup = self.medicaments[id_medicaments[str(medicament.medicine.id)]].qty + medicament.qty
                    self.medicaments[id_medicaments[str(medicament.medicine.id)]].qty = qty_sup
                    self.medicaments = [(2, medicament.id, False)]
                else:
                    id_medicaments[str(medicament.medicine.id)] = inx
                    # print('chưa có')
                inx += 1

    def write(self, vals):
        res = super(SHealthPatientRoundingManagement, self).write(vals)
        for record in self.with_env(self.env(su=True)):
            if vals.get('evaluation_start_date') or vals.get('evaluation_end_date'):
                evaluation_start_date = vals.get('evaluation_start_date') or record.evaluation_start_date
                evaluation_end_date = vals.get('evaluation_end_date') or record.evaluation_end_date

                # format to date
                if isinstance(evaluation_start_date, str):
                    evaluation_start_date = datetime.datetime.strptime(evaluation_start_date, '%Y-%m-%d %H:%M:%S')
                if isinstance(evaluation_end_date, str):
                    evaluation_end_date = datetime.datetime.strptime(evaluation_end_date, '%Y-%m-%d %H:%M:%S')

                if evaluation_start_date and evaluation_end_date and (evaluation_start_date > evaluation_end_date):
                    raise UserError(
                        _('Thông tin không hợp lệ! Ngày giờ bắt đầu phải trước ngày kết thúc phẫu thuật!'))

            if vals.get('services'):
                # check dịch vụ đổi trong phiếu chuyên khoa: nếu xóa sẽ xóa dv sẽ xóa ở dv ở thành viên tham gia
                # thành viên tham gia
                for rounding_mem in record.rounding_team.mapped('service_performances').ids:
                    if rounding_mem not in record.services.ids:
                        record.rounding_team.write({'service_performances': [(3, rounding_mem)]})

                # vtth
                for supply_cshp in record.medicaments.mapped('services').ids:
                    if supply_cshp not in record.services.ids:
                        record.medicaments.write({'services': [(3, supply_cshp)]})

        return res

    # Preventing deletion of a rounding details which is not in draft state
    def unlink(self):
        for nursing in self.filtered(lambda nursing: nursing.state not in ['Draft']):
            raise UserError(_('You can not delete rounding information which is not in "Draft" state !!'))
        return super(SHealthPatientRoundingManagement, self).unlink()

    def reset_all_supply(self):
        for rounding in self.filtered(lambda r: r.state not in ['Completed']):
            rounding.medicaments = False

    @api.model
    def create(self, vals):
        inpatient_detail = self.env['sh.medical.inpatient'].search([('id', '=', vals['inpatient_id'])], limit=1)
        sequence = self.env['ir.sequence'].next_by_code(
            'sh.medical.patient.rounding.%s' % inpatient_detail.institution.id)
        if not sequence:
            raise ValidationError(_('Định danh phiếu chi tiết chăm sóc của Cơ sở y tế này đang không tồn tại!'))
        vals['name'] = sequence
        # Tự động lấy bom mặc định
        result_bom_ids = self.env['sh.medical.product.bundle']
        if 'services' in vals and vals['services']:
            for service in vals['services'][0][2]:
                other_bom = self.env['sh.medical.product.bundle'].search(
                    [('service_id', '=', service), ('type', '=', 'Inpatient'),
                     ('region', '=', inpatient_detail.institution.region)],
                    limit=1)
                if other_bom:
                    result_bom_ids += other_bom
            vals.update({
                'other_bom': [[6, 0, result_bom_ids.ids]]
            })
        # if result_bom_ids:
        #     self.medicaments = False
        #     supplies = []
        #     check_duplicate = []
        #     Room = self.env['sh.medical.health.center.ot']
        #     for record in result_bom_ids:
        #         for record_line in record.products.filtered(lambda p: p.note == 'Inpatient'):
        #             location = inpatient_detail.room.location_supply_stock or Room.browse(
        #                 self.env.context.get('room')).location_supply_stock
        #             if record_line.product_id.medicament_type == 'Medicine':
        #                 location = inpatient_detail.room.location_medicine_stock or Room.browse(
        #                     self.env.context.get('room')).location_medicine_stock
        #             if location:
        #                 qty = record_line.quantity
        #                 mats_id = record_line.product_id.id
        #                 if mats_id not in check_duplicate:
        #                     check_duplicate.append(mats_id)
        #                     supplies.append((0, 0, {'medicine': mats_id,
        #                                             'init_qty': qty,
        #                                             'qty': qty,
        #                                             'uom_id': record_line.uom_id.id,
        #                                             'location_id': location.id,
        #                                             'indications': record_line.product_id.indications,
        #                                             'dosage': record_line.product_id.dosage,
        #                                             'services': [(4, record.service_id.id)],
        #                                             'notes': record_line.note}))
        #                 else:
        #                     old_supply_index = check_duplicate.index(mats_id)
        #                     supplies[old_supply_index][2]['services'] += [(4, record.service_id.id)]
        #                     supplies[old_supply_index][2]['init_qty'] += qty
        #                     supplies[old_supply_index][2]['qty'] += qty
            # vals.update({
            #     'medicaments': supplies
            # })
        print('vals', vals)
        return super(SHealthPatientRoundingManagement, self).create(vals)

    def reverse_materials(self):
        num_of_location = len(self.medicaments.mapped('location_id'))
        pick_need_reverses = self.env['stock.picking'].search([('origin', 'ilike', 'THHP - %s - %s' % (self.name,self.inpatient_id.name)),('company_id','=',self.env.company.id)], order='create_date DESC', limit=num_of_location)
        if pick_need_reverses:
            for pick_need_reverse in pick_need_reverses:
                date_done = pick_need_reverse.date_done

                fail_pick_count = self.env['stock.picking'].search_count([('name', 'ilike', pick_need_reverse.name), ('company_id', '=', self.env.company.id)])
                pick_need_reverse.name += '-FP%s' % fail_pick_count
                pick_need_reverse.move_ids_without_package.write(
                    {'reference': pick_need_reverse.name})  # sửa cả trường tham chiếu của move.line (Dịch chuyển kho)

                new_wizard = self.env['stock.return.picking'].new({'picking_id': pick_need_reverse.id})  # tạo new wizard chưa lưu vào db
                new_wizard._onchange_picking_id()  # chạy hàm onchange với tham số ở trên
                wizard_vals = new_wizard._convert_to_write(new_wizard._cache)  # lấy dữ liệu sau khi đã chạy qua onchange
                wizard = self.env['stock.return.picking'].with_context(reopen_flag=True, no_check_quant=True).create(wizard_vals)
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


    def set_to_draft(self):
        # mở lại phiếu
        self.reverse_materials()
        self.inpatient_id.walkin.update_walkin_material(mats_types=['Inpatient'])
        res = self.write({'state': 'Draft'})

    def check_have_record(self,record):
        if isinstance(record.id, models.NewId):
            res = super(SHealthPatientRoundingManagement, self).create({
                'patient': self.patient.id,
                'doctor': self.doctor.id,
                'inpatient_id': self.inpatient_id.id,
                'evaluation_start_date': self.evaluation_start_date,
                'evaluation_end_date': self.evaluation_end_date,
                'temperature': self.temperature,
                'bpm': self.bpm,
                'respiratory_rate': self.respiratory_rate,
                'systolic': self.systolic,
                'diastolic': self.diastolic,
                'osat': self.osat,
                'evolution': self.evolution,
                'round_summary': self.round_summary,
                'execute': self.execute,
                'medicaments': self.medicaments.ids,
            })
            return res
        else:
            return record


    def set_to_completed(self):
        # neu data phiếu chăm sóc chưa được tạo thì gọi hàm tạo
        res = self.check_have_record(self)

        # tru vat tu theo tieu hao của phiếu chi tiet cham soc hau phau
        if res.evaluation_end_date:
            evaluation_end_date = res.evaluation_end_date
        else:
            evaluation_end_date = res.evaluation_start_date if res.evaluation_start_date else fields.Datetime.now()
        if evaluation_end_date > datetime.datetime.now():
            raise ValidationError('Bạn không thể đóng phiếu CSHP do ngày giờ kết thúc lớn hơn ngày giờ hiện tại!')

        # 20220320 - tungnt - onnet
        default_production_location = self.env['stock.location'].get_default_production_location_per_company()

        vals = {}
        validate_str = ''
        for mat in res.medicaments:
            if mat.qty > 0:  # CHECK SO LUONG SU DUNG > 0
                quantity_on_hand = self.env['stock.quant']._get_available_quantity(mat.medicine.product_id,
                                                                                   mat.location_id)  # check quantity trong location
                if mat.uom_id != mat.medicine.uom_id:
                    mat.write({'qty': mat.uom_id._compute_quantity(mat.qty, mat.medicine.uom_id),
                               'uom_id': mat.medicine.uom_id.id})  # quy so suong su dung ve don vi chinh cua san pham

                if quantity_on_hand < mat.qty:
                    validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
                            mat.medicine.default_code, mat.medicine.name, str(quantity_on_hand), str(mat.uom_id.name), mat.location_id.name)
                else:  # truong one2many trong stock picking de tru cac product trong inventory
                    sub_vals = {
                        'name': 'THHP: ' + mat.medicine.product_id.name,
                        'origin': res.name,
                        'date': evaluation_end_date,
                        'company_id': self.env.company.id,
                        'date_expected': evaluation_end_date,
                        # 'date_done': evaluation_end_date,
                        'product_id': mat.medicine.product_id.id,
                        'product_uom_qty': mat.qty,
                        'product_uom': mat.uom_id.id,
                        'location_id': mat.location_id.id,
                        'location_dest_id': default_production_location.id,
                        'partner_id': res.patient.partner_id.id,
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
                                                                   self.inpatient_id.institution.warehouse_ids[0].id)],
                                                                 limit=1).id
            # picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
            #                                                       ('warehouse_id', '=',
            #                                                        self.env.ref('stock.warehouse0').id)],
            #                                                      limit=1).id
            for location_key in vals:
                pick_note = 'THHP - %s - %s - %s' % (
                res.name, res.inpatient_id.name, location_key)
                pick_vals = {'note': pick_note,
                             'origin': pick_note,
                             'partner_id': res.patient.partner_id.id,
                             'patient_id': self.patient.id,
                             'picking_type_id': picking_type,
                             'location_id': int(location_key),
                             'location_dest_id': default_production_location.id,
                             'date_done': evaluation_end_date,
                             # 'immediate_transfer': True,  # sẽ gây lỗi khi dùng lô, pick với immediate_transfer sẽ ko cho tạo move, chỉ tạo move line
                             # 'move_ids_without_package': vals[location_key]
                             }
                fail_pick_name = self.env['stock.picking'].search(
                    [('origin', 'ilike', 'THHP - %s - %s - %s' % (res.name, res.inpatient_id.name, location_key))],
                    limit=1).name
                if fail_pick_name:
                    pick_vals['name'] = fail_pick_name.split('-', 1)[0]
                stock_picking = self.env['stock.picking'].create(pick_vals)
                for move_val in vals[location_key]:
                    move_val['name'] = stock_picking.name + " - " + move_val['name']
                    move_val['picking_id'] = stock_picking.id
                    self.env['stock.move'].create(move_val)

                # KO TU DONG XUAT KHO NUA MA CHI TAO PHIEU XUAT THOI
                stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
                for move_line in stock_picking.move_ids_without_package:
                    for move_live_detail in move_line.move_line_ids:
                        move_live_detail.qty_done = move_live_detail.product_uom_qty
                    # move_line.quantity_done = move_line.product_uom_qty
                stock_picking.with_context(force_period_date=evaluation_end_date).sudo().button_validate()  # ham tru product trong inventory, sudo để đọc stock.valuation.layer

                # sua ngay hoan thanh
                for move_line in stock_picking.move_ids_without_package:
                    move_line.move_line_ids.write({'date': evaluation_end_date})  # sửa ngày hoàn thành ở stock move line
                stock_picking.move_ids_without_package.write(
                    {'date': evaluation_end_date})  # sửa ngày hoàn thành ở stock move
                stock_picking.date_done = evaluation_end_date
                stock_picking.sci_date_done = evaluation_end_date

                stock_picking.create_date = res.evaluation_start_date
                # Cập nhật ngược lại picking_id vào mats để truyền số liệu sang vật tư phiếu khám
                res.medicaments.filtered(lambda m: m.location_id.id == int(location_key)).write({'picking_id': stock_picking.id})

        elif validate_str != '':
            raise ValidationError(_(
                "Các loại Thuốc và Vật tư sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))

        res.write({'state': 'Completed', 'evaluation_end_date': evaluation_end_date})

        # cap nhat vat tu cho phieu kham
        res.inpatient_id.walkin.update_walkin_material(mats_types=['Inpatient'])

        # log access patient
        # data_log = self.env['sh.medical.patient.log'].search([('walkin', '=', res.inpatient_id.walkin.id)])
        # data_hp = False
        # for data in data_log:
        #     # nếu đã có data log cho ck khoa này rồi
        #     if data.department.id == res.inpatient_id.ward.id:
        #         data_hp = data
        # # nếu chưa có data log=> tạo log
        # if not data_hp:
        #     vals_log = {'walkin': res.inpatient_id.walkin.id,
        #                 'patient': res.patient.id,
        #                 'department': res.inpatient_id.ward.id,
        #                 'date_in': res.evaluation_start_date,
        #                 'date_out': res.evaluation_end_date}
        #     self.env['sh.medical.patient.log'].create(vals_log)
        # else:
        #     data_hp.date_out = res.evaluation_end_date


    def print_patient_evaluation(self):
        return self.env.ref('shealth_all_in_one.action_report_patient_rounding_evaluation').report_action(self)

    def view_detail_rounding(self):
        return {
            'name': _('Chi tiết chăm sóc'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_rounding_view').id,
            'res_model': 'sh.medical.patient.rounding',  # model want to display
            'target': 'current',  # if you want popup,
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': self.id
        }

class SHealthPatientInstructionMedicines(models.Model):
    _name = 'sh.medical.patient.instruction.medicines'
    _description = 'Patient Medicines For Instruction'

    MEDICAMENT_TYPE = [
        ('Medicine', 'Medicine'),
        ('Supplies', 'Supplies'),
        ('CCDC', 'CCDC')
    ]

    name = fields.Many2one('sh.medical.patient.instruction', string='Instruction')
    medicine = fields.Many2one('sh.medical.medicines', string='Medicines and Supply', domain=lambda self:[('categ_id','child_of',self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)], required=True)
    # medicine = fields.Many2one('sh.medical.medicines', string='Medicines', domain=[('medicament_type','=','Medicine')], required=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    qty = fields.Float("Quantity", digits='Product Unit of Measure',default=lambda *a: 1)
    qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
                             compute='compute_available_qty_supply')
    notes = fields.Text('Comment')

    location_id = fields.Many2one('stock.location', 'Stock location', domain="[('usage', '=', 'internal')]")
    medicament_type = fields.Selection(MEDICAMENT_TYPE, related="medicine.medicament_type", string='Medicament Type',
                                       store=True)

    services = fields.Many2many('sh.medical.health.center.service', 'sh_instruction_medicines_service_rel', track_visibility='onchange',
                                string='Dịch vụ thực hiện')
    service_related = fields.Many2many('sh.medical.health.center.service', 'sh_instruction_medicines_service_related_rel', related="name.services",
                                       string='Dịch vụ liên quan')

    picking_id = fields.Many2one('stock.picking', string='Phiếu điều chuyển')

    @api.depends('medicine')
    def compute_available_qty_supply(self):
        for record in self:
            record.qty_avail = record.medicine.qty_available if record.medicine else 0

    @api.onchange('qty', 'medicine')
    def onchange_qty(self):
        if self.qty < 0 and self.medicine:
            raise UserError(_("Số lượng nhập phải lớn hơn 0!"))

    @api.onchange('medicine')
    def _change_product_id(self):
        domain = {'domain': {'uom_id': [('category_id', '=', self.medicine.uom_id.category_id.id)]}}
        institution = self.name.inpatient_id.institution
        room = self.name.inpatient_id.bed.room
        self.uom_id = self.medicine.uom_id
        if self.medicament_type == 'Medicine':
            self.location_id = room.location_medicine_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'medicine'), ('company_id', '=', institution.his_company.id)]
        elif self.medicament_type == 'Supplies':
            self.location_id = room.location_supply_stock.id
            domain['domain']['location_id'] = [('location_institution_type', '=', 'supply'), ('company_id', '=', institution.his_company.id)]
        return domain


class SHealthPatientInstructionManagement(models.Model):
    _name = 'sh.medical.patient.instruction'
    _description = 'Patient Doctor Instruction Management'

    _order = "name"

    STATUS = [
        ('Draft', 'Draft'),
        ('Completed', 'Completed'),
    ]

    EVOLUTION = [
        ('Status Quo', 'Status Quo'),
        ('Improving', 'Improving'),
        ('Worsening', 'Worsening'),
    ]


    def _get_patient_instruction(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    def get_anesthetist(self):
        if self.env.ref('shealth_all_in_one.5', False):
            return [('is_pharmacist', '=', False), ('speciality', '=', self.env.ref('shealth_all_in_one.5').id)]
        else:
            return [('is_pharmacist', '=', False)]

    name = fields.Char(string='Instruction #', size=128, readonly=True, default=lambda *a: '/')
    inpatient_id = fields.Many2one('sh.medical.inpatient', string='Registration Code', required=True, readonly=True, states={'Draft': [('readonly', False)]})
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True, states={'Draft': [('readonly', False)]})
    doctor = fields.Many2one('sh.medical.physician', string='Physician', help="Physician Name", domain=lambda self: self.get_anesthetist(),
                             required=True, readonly=True,states={'Draft': [('readonly', False)]}, default=_get_patient_instruction)
    evaluation_start_date = fields.Datetime(string='Start date & time', required=True, readonly=True, states={'Draft': [('readonly', False)]}, default=lambda *a: datetime.datetime.now())
    evaluation_end_date = fields.Datetime(string='End date & time', readonly=True, states={'Draft': [('readonly', False)]})
    evolution = fields.Selection(EVOLUTION, string='Evolution', readonly=True, states={'Draft': [('readonly', False)]})
    round_summary = fields.Text(string="Round Summary", readonly=True, states={'Draft': [('readonly', False)]})
    ins_medicaments = fields.One2many('sh.medical.patient.instruction.medicines', 'name', string='Medicines', help="List of the medicines assigned in this instruction", readonly=True, states={'Draft': [('readonly', False)]})
    state = fields.Selection(STATUS, string='State',readonly=True, default=lambda *a: 'Draft')

    services = fields.Many2many('sh.medical.health.center.service', 'sh_instruction_service_rel', track_visibility='onchange',
                                string='Dịch vụ thực hiện')
    service_related = fields.Many2many('sh.medical.health.center.service', 'sh_instruction_service_related_rel', related="inpatient_id.services",
                                       string='Dịch vụ liên quan')

    #  check công ty hiện tại của người dùng với công ty của phiếu
    check_current_company = fields.Boolean(string='Cty hiện tại', compute='_check_current_company')

    @api.depends('inpatient_id.institution.his_company')
    def _check_current_company(self):
        for record in self:
            record.check_current_company = True if record.inpatient_id.institution.his_company == self.env.company else False

    @api.onchange('evaluation_start_date')
    def _onchange_date(self):
        if not self.evaluation_end_date:
            self.evaluation_end_date = self.evaluation_start_date


    # Preventing deletion of a rounding details which is not in draft state
    def unlink(self):
        for nursing in self.filtered(lambda nursing: nursing.state not in ['Draft']):
            raise UserError(_('You can not delete instruction information which is not in "Draft" state !!'))
        return super(SHealthPatientInstructionManagement, self).unlink()

    @api.model
    def create(self, vals):
        inpatient_detail = self.env[''].search([('id', '=', vals['inpatient_id'])], limit=1)
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.patient.instruction.%s'%inpatient_detail.institution.id)
        if not sequence:
            raise ValidationError(_('Định danh phiếu chi tiết y lệnh của Cơ sở y tế này đang không tồn tại!'))

        vals['name'] = sequence
        return super(SHealthPatientInstructionManagement, self).create(vals)

    def reverse_materials(self):
        num_of_location = len(self.ins_medicaments.mapped('location_id'))
        pick_need_reverses = self.env['stock.picking'].search([('origin', 'ilike', 'THHP - %s - %s' % (self.name,self.inpatient_id.name)),('company_id','=',self.env.company.id)], order='create_date DESC', limit=num_of_location)
        if pick_need_reverses:
            for pick_need_reverse in pick_need_reverses:
                date_done = pick_need_reverse.date_done

                fail_pick_count = self.env['stock.picking'].search_count([('name', 'ilike', pick_need_reverse.name), ('company_id', '=', self.env.company.id)])
                pick_need_reverse.name += '-FP%s' % fail_pick_count
                pick_need_reverse.move_ids_without_package.write(
                    {'reference': pick_need_reverse.name})  # sửa cả trường tham chiếu của move.line (Dịch chuyển kho)

                new_wizard = self.env['stock.return.picking'].new({'picking_id': pick_need_reverse.id})  # tạo new wizard chưa lưu vào db
                new_wizard._onchange_picking_id()  # chạy hàm onchange với tham số ở trên
                wizard_vals = new_wizard._convert_to_write(new_wizard._cache)  # lấy dữ liệu sau khi đã chạy qua onchange
                wizard = self.env['stock.return.picking'].with_context(reopen_flag=True, no_check_quant=True).create(wizard_vals)
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


    def set_to_draft(self):
        # mở lại phiếu
        self.reverse_materials()
        self.inpatient_id.walkin.update_walkin_material(mats_types=['Inpatient'])
        res = self.write({'state': 'Draft'})

    def check_have_record(self,record):
        if isinstance(record.id, models.NewId):
            res = super(SHealthPatientInstructionManagement, self).create({
                'patient': record.patient.id,
                'doctor': record.doctor.id,
                'inpatient_id': record.inpatient_id.id,
                'evaluation_start_date': record.evaluation_start_date,
                'evaluation_end_date': record.evaluation_end_date,
                'round_summary': record.round_summary,
                'evolution': record.evolution,
                'ins_medicaments': record.ins_medicaments.ids,
            })
            return res
        else:
            return record

    def set_to_completed(self):
        # neu data phiếu y lệnh chưa được tạo thì gọi hàm tạo
        res = self.check_have_record(self)

        # tru vat tu theo tieu hao của phiếu chi tiet cham soc hau phau
        if res.evaluation_end_date:
            evaluation_end_date = res.evaluation_end_date
        else:
            evaluation_end_date = res.evaluation_start_date if res.evaluation_start_date else fields.Datetime.now()

        vals = {}
        validate_str = ''
        for mat in res.ins_medicaments:
            if mat.qty > 0:  # CHECK SO LUONG SU DUNG > 0
                quantity_on_hand = self.env['stock.quant']._get_available_quantity(mat.medicine.product_id,
                                                                                   mat.location_id)  # check quantity trong location
                if mat.uom_id != mat.medicine.uom_id:
                    mat.write({'qty': mat.uom_id._compute_quantity(mat.qty, mat.medicine.uom_id),
                               'uom_id': mat.medicine.uom_id.id})  # quy so suong su dung ve don vi chinh cua san pham

                if quantity_on_hand < mat.qty:
                    validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
                            mat.medicine.default_code, mat.medicine.name, str(quantity_on_hand), str(mat.uom_id.name), mat.location_id.name)
                else:  # truong one2many trong stock picking de tru cac product trong inventory
                    sub_vals = {
                        'name': 'THHP: ' + mat.medicine.product_id.name,
                        'origin': res.name,
                        'date': evaluation_end_date,
                        'company_id': self.env.company.id,
                        'date_expected': evaluation_end_date,
                        # 'date_done': evaluation_end_date,
                        'product_id': mat.medicine.product_id.id,
                        'product_uom_qty': mat.qty,
                        'product_uom': mat.uom_id.id,
                        'location_id': mat.location_id.id,
                        'location_dest_id': res.patient.partner_id.property_stock_customer.id,
                        'partner_id': res.patient.partner_id.id,
                        # xuat cho khach hang/benh nhan nao
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
                                                                   self.inpatient_id.walkin.institution.warehouse_ids[0].id)],
                                                                 limit=1).id
            # picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
            #                                                       ('warehouse_id', '=',
            #                                                        self.env.ref('stock.warehouse0').id)],
            #                                                      limit=1).id
            for location_key in vals:
                pick_note = 'THHP - %s - %s - %s' % (
                res.name, res.inpatient_id.name, location_key)
                pick_vals = {'note': pick_note,
                             'origin': pick_note,
                             'partner_id': res.patient.partner_id.id,
                             'patient_id': res.patient.id,
                             'picking_type_id': picking_type,
                             'location_id': int(location_key),
                             'location_dest_id': res.patient.partner_id.property_stock_customer.id,
                             'date_done': evaluation_end_date,
                             # 'immediate_transfer': True,  # sẽ gây lỗi khi dùng lô, pick với immediate_transfer sẽ ko cho tạo move, chỉ tạo move line
                             # 'move_ids_without_package': vals[location_key]
                             }
                fail_pick_name = self.env['stock.picking'].search(
                    [('origin', 'ilike', 'THHP - %s - %s - %s' % (res.name, res.inpatient_id.name, location_key))],
                    limit=1).name
                if fail_pick_name:
                    pick_vals['name'] = fail_pick_name.split('-', 1)[0]
                stock_picking = self.env['stock.picking'].create(pick_vals)
                for move_val in vals[location_key]:
                    move_val['name'] = stock_picking.name + " - " + move_val['name']
                    move_val['picking_id'] = stock_picking.id
                    self.env['stock.move'].create(move_val)

                # KO TU DONG XUAT KHO NUA MA CHI TAO PHIEU XUAT THOI
                stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
                for move_line in stock_picking.move_ids_without_package:
                    for move_live_detail in move_line.move_line_ids:
                        move_live_detail.qty_done = move_live_detail.product_uom_qty
                    # move_line.quantity_done = move_line.product_uom_qty
                stock_picking.with_context(force_period_date=evaluation_end_date).sudo().button_validate()  # ham tru product trong inventory, sudo để đọc stock.valuation.layer

                # sua ngay hoan thanh
                for move_line in stock_picking.move_ids_without_package:
                    move_line.move_line_ids.write({'date': evaluation_end_date})  # sửa ngày hoàn thành ở stock move line
                stock_picking.move_ids_without_package.write(
                    {'date': evaluation_end_date})  # sửa ngày hoàn thành ở stock move
                stock_picking.date_done = evaluation_end_date
                stock_picking.sci_date_done = evaluation_end_date

                stock_picking.create_date = res.evaluation_start_date

                # Cập nhật ngược lại picking_id vào mats để truyền số liệu sang vật tư phiếu khám
                res.ins_medicaments.filtered(lambda m: m.location_id.id == int(location_key)).write({'picking_id': stock_picking.id})

        elif validate_str != '':
            raise ValidationError(_(
                "Các loại Thuốc và Vật tư sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))

        res.write({'state': 'Completed', 'evaluation_end_date': evaluation_end_date})

        # cap nhat vat tu cho phieu kham
        res.inpatient_id.walkin.update_walkin_material(mats_types=['Inpatient'])

    def print_patient_instruction(self):
        return self.env.ref('shealth_all_in_one.action_report_patient_instruction').report_action(self)


class SHealthInpatient(models.Model):
    _inherit = 'sh.medical.inpatient'

    roundings = fields.One2many('sh.medical.patient.rounding', 'inpatient_id', string='Roundings Details', readonly=True,
                                states={'Draft': [('readonly', False)], 'Hospitalized': [('readonly', False)]})

    instructions = fields.One2many('sh.medical.patient.instruction', 'inpatient_id', string='Instruction Details', readonly=True,
                                   states={'Draft': [('readonly', False)], 'Hospitalized': [('readonly', False)]})

    def set_to_discharged(self):
        for inpatient in self:
            # còn y lệnh chưa xác nhận
            if len(inpatient.instructions.filtered(lambda ints: ints.state == "Draft")) > 0:
                raise UserError(_('Bạn không thể xác nhận kết thúc chăm sóc cho bệnh nhân khi có y lệnh chưa được xác nhận!'))

            # còn csph chưa xác nhận
            if len(inpatient.roundings.filtered(lambda rounds: rounds.state == "Draft")) > 0:
                raise UserError(
                    _('Bạn không thể xác nhận kết thúc chăm sóc cho bệnh nhân khi có phiếu cshp chưa được xác nhận!'))

        return super(SHealthInpatient, self).set_to_discharged()

    def get_total_nursing_day(self):
        for record in self:
            group_list_labs = self.env['sh.medical.patient.rounding'].read_group([('id', 'in', record.roundings.ids)], ['id'], ['evaluation_start_date:day'])
            if group_list_labs:
                return len(group_list_labs)
            else:
                return 0

# Patient Ambulatory Care Management

# class SHealthPatientAmbulatoryProcedures(models.Model):
#     _name = 'sh.medical.patient.ambulatory.procedure'
#     _description = 'Patient Procedures For Ambulatory'
#
#     name = fields.Many2one('sh.medical.patient.ambulatory', string='Ambulatory')
#     procedures = fields.Many2one('sh.medical.procedure', string='Procedures', required=True)
#     notes = fields.Text('Notes')
#
#
# class SHealthPatientAmbulatoryMedicines(models.Model):
#     _name = 'sh.medical.patient.ambulatory.medicines'
#     _description = 'Patient Medicines For Ambulatory'
#
#     name = fields.Many2one('sh.medical.patient.ambulatory', string='Ambulatory')
#     medicine = fields.Many2one('sh.medical.medicines', string='Medicines', domain=[('medicament_type','=','Medicine')], required=True)
#     qty = fields.Integer(string="Quantity", default=lambda *a: 1)
#     notes = fields.Text(string='Comment')
#
#
# class SHealthPatientAmbulatoryCare(models.Model):
#     _name = 'sh.medical.patient.ambulatory'
#     _description = 'Patient Ambulatory Management'
#
#     STATUS = [
#         ('Draft', 'Draft'),
#         ('Completed', 'Completed'),
#     ]
#
#     EVOLUTION = [
#         ('Initial', 'Initial'),
#         ('Status Quo', 'Status Quo'),
#         ('Improving', 'Improving'),
#         ('Worsening', 'Worsening'),
#     ]
#
#
#     def _get_patient_ambulatory(self):
#         """Return default physician value"""
#         therapist_obj = self.env['sh.medical.physician']
#         domain = [('sh_user_id', '=', self.env.uid)]
#         user_ids = therapist_obj.search(domain)
#         if user_ids:
#             return user_ids.id or False
#         else:
#             return False
#
#     name = fields.Char(string='Session #', size=128, readonly=True, default=lambda *a: '/')
#     evaluation_id = fields.Many2one('sh.medical.evaluation', string='Evaluation #', required=True, readonly=True, states={'Draft': [('readonly', False)]})
#     base_condition = fields.Many2one('sh.medical.pathology', string='Condition', required=True, readonly=True, states={'Draft': [('readonly', False)]})
#     patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True, states={'Draft': [('readonly', False)]})
#     doctor = fields.Many2one('sh.medical.physician', string='Physician', help="Physician Name", domain=[('is_pharmacist','=',False)], required=True, readonly=True,states={'Draft': [('readonly', False)]}, default=_get_patient_ambulatory)
#     ordering_doctor = fields.Many2one('sh.medical.physician', string='Requested by', help="Physician Name", domain=[('is_pharmacist','=',False)], readonly=True,states={'Draft': [('readonly', False)]})
#     evaluation_start_date = fields.Datetime(string='Start date & time', required=True, readonly=True, states={'Draft': [('readonly', False)]}, default= lambda *a: datetime.datetime.now())
#     evaluation_end_date = fields.Datetime(string='End date & time', readonly=True, states={'Draft': [('readonly', False)]})
#     systolic = fields.Integer(string='Systolic Pressure', readonly=True, states={'Draft': [('readonly', False)]})
#     diastolic = fields.Integer(string='Diastolic Pressure', readonly=True, states={'Draft': [('readonly', False)]})
#     bpm = fields.Integer(string='Heart Rate', help="Heart rate expressed in beats per minute", readonly=True, states={'Draft': [('readonly', False)]})
#     respiratory_rate = fields.Integer(string='Respiratory Rate', help="Respiratory rate expressed in breaths per minute", readonly=True, states={'Draft': [('readonly', False)]})
#     osat = fields.Integer(string='Oxygen Saturation', help="Oxygen Saturation(arterial)", readonly=True, states={'Draft': [('readonly', False)]})
#     temperature = fields.Float(string='Temperature', help="Temperature in celsius", readonly=True, states={'Draft': [('readonly', False)]})
#     glycemia = fields.Integer(string='Glycemia', help="Blood Glucose level", readonly=True, states={'Draft': [('readonly', False)]})
#     evolution = fields.Selection(EVOLUTION, string='Evolution', readonly=True, states={'Draft': [('readonly', False)]})
#     session_notes = fields.Text(string="Notes", readonly=True, states={'Draft': [('readonly', False)]})
#     procedures = fields.One2many('sh.medical.patient.ambulatory.procedure', 'name', string='Procedures', help="List of the procedures in this ambulatory. Please enter the first one as the main procedure", readonly=True, states={'Draft': [('readonly', False)]})
#     medicaments = fields.One2many('sh.medical.patient.ambulatory.medicines', 'name', string='Medicines', help="List of the medicines assigned in this ambulatory", readonly=True, states={'Draft': [('readonly', False)]})
#     state = fields.Selection(STATUS, string='State',readonly=True, default=lambda *a: 'Draft')
#
#
#     # Preventing deletion of a ambulatory care details which is not in draft state
#
#     def unlink(self):
#         for nursing in self.filtered(lambda nursing: nursing.state not in ['Draft']):
#             raise UserError(_('You can not delete information which is not in "Draft" state !!'))
#         return super(SHealthPatientAmbulatoryCare, self).unlink()
#
#
#     @api.model
#     def create(self, vals):
#         sequence = self.env['ir.sequence'].next_by_code('sh.medical.patient.ambulatory')
#         vals['name'] = sequence
#         return super(SHealthPatientAmbulatoryCare, self).create(vals)
#
#
#
#     def set_to_completed(self):
#         return self.write({'state': 'Completed','evaluation_end_date': datetime.datetime.now()})
