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

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
from odoo.osv import expression


class ProductBundle(models.Model):
    _name = 'sh.medical.product.bundle'
    _description = "All BOM of the service"

    TYPE = [
        ('Labtest', 'Vật tư xét nghiệm'),
        ('Imaging', 'Vật tư CĐHA'),
        ('Surgery', 'Vật tư Phẫu thuật'),
        ('Specialty', 'Vật tư chuyên khoa'),
        ('Inpatient', 'Vật tư Lưu bệnh nhân'),
        ('Evaluation', 'Vật tư của Tái khám'),
        ('Medicine', 'Thuốc cấp về')
    ]

    REGION = [
        ('North', 'Miền Bắc'),
        ('South', 'Miền Nam')
    ]

    name = fields.Char("BOM's name")
    code = fields.Char("BOM's code")
    region = fields.Selection(REGION,"Miền",help="BOM dùng cho vùng miền nào?")
    type = fields.Selection(TYPE,"Loại",help="BOM dùng cho loại phiếu tiêu hao nào?")
    service_id = fields.Many2one('sh.medical.health.center.service', 'Service', ondelete='cascade')
    duplicate = fields.Many2one('sh.medical.product.bundle', string='Duplicate from')
    products = fields.One2many('sh.medical.products.line', 'bundle', string='Product')
    products_domain = fields.Many2many('sh.medical.medicines', string='Product domain', compute='_get_products_domain')
    active = fields.Boolean('Có hiệu lực', default=True)

    @api.onchange('type')
    def onchange_type(self):
        if self.products:
            for product in self.products:
                product.note = self.type

    @api.depends('products')
    def _get_products_domain(self):
        for record in self:
            record.products_domain = []
            if len(record.products) > 0:
                record.products_domain = [(6, 0, [product.product_id.id for product in record.products if product.product_id])]

    @api.onchange('duplicate')
    def onchange_duplicate(self):
        if self.duplicate:
            # model = self._context.get('active_model')
            # current_record = self.env['op.admission'].browse(self._context.get('active_id'))
            # self.name = self.duplicate.name + ' - '
            vals = []
            for record in self.env['sh.medical.products.line'].search([('bundle', '=', self.duplicate.id)]):
                vals.append((0, 0, {'product_id': record.product_id.id,
                                    'quantity': record.quantity,
                                    'uom_id': record.uom_id,
                                    # 'location_id': record.location_id,
                                    'dosage': record.dosage,
                                    'note': record.note}))
            self.update({'products': vals})
        if not self.duplicate and len(self.products) > 0:
            for record in self.products:
                record.unlink()

    @api.depends('products')
    def _get_total_cost(self):
        for record in self:
            for product in record.products:
                record.total_cost += product.cost * product.quantity

    @api.depends('products')
    def _get_total_price(self):
        for record in self:
            for product in record.products:
                self.total_price += product.price * product.quantity


class ProductsLine(models.Model):
    _name = 'sh.medical.products.line'
    _description = "All BOM line of the service"

    NOTE = [
        ('Labtest', 'Material of Labtest'),
        ('Imaging', 'Material of Imaging'),
        ('Surgery', 'Material of Surgery'),
        ('Specialty', 'Material of Specialty Service'),
        ('Inpatient', 'Material of Inpatient'),
        ('Evaluation', 'Vật tư của Tái khám'),
        ('Medicine', 'Thuốc cấp về'),
        # ('Extra', 'Material of Extra Service'),
    ]

    bundle = fields.Many2one('sh.medical.product.bundle', ondelete='cascade')
    bundle_code = fields.Char(related='bundle.code', store=True)
    bundle_service = fields.Many2one(related='bundle.service_id', store=True)
    product_id = fields.Many2one('sh.medical.medicines', string='Product')
    quantity = fields.Float('Quantity', digits='Product Unit of Measure', default=1)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    # location_id = fields.Many2one('stock.location', 'Stock location', domain="[('usage', '=', 'internal')]")
    note = fields.Selection(NOTE, 'Material note', related="bundle.type", store=True)
    dosage = fields.Text('Cách sử dụng')

    @api.onchange('product_id')
    def _change_product_id(self):
        self.uom_id = self.product_id.uom_id

        return {'domain': {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.product_id.uom_id.category_id:
            self.uom_id = self.product_id.uom_id
            raise Warning(
                _('The Service Unit of Measure and the Material Unit of Measure must be in the same category.'))


    # @api.onchange('product')
    # def _onchange(self):
    #     for record in self:
    #         if record.product:
    #             record.cost = record.product.standard_price
    #             record.price = record.product.lst_price


    @api.constrains('quantity')
    def validate_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero!"))

    _sql_constraints = [
        ('product_BOM_uniq', 'unique(product_id, bundle)', 'Product must be unique per BOM!')
    ]

class ScriptPhoneCall(models.Model):
    _name = 'crm.script.phone.call'
    _description = 'Script Phone Call'

    code = fields.Char('Mã kịch bản', required=True)
    name = fields.Char('Tên kịch bản', required=True)
    _sql_constraints = [('unique_code', 'unique(code)', 'Mã đã tồn tại!!.')]

    def name_get(self):
        return [(template.id, '%s%s' % (template.code and '[%s] ' % template.code or '', template.name))
                for template in self]

class SHealthReExamService(models.Model):
    _name = 'sh.medical.health.center.service.reexam'
    _description = "Lịch tái khám theo dịch vụ"

    NOTE = [
        ('Check', 'Chăm sóc lần 1'),
        ('Check1', 'Chăm sóc lần 2'),
        ('Check2', 'Chăm sóc lần 3'),
        ('Check3', 'Chăm sóc lần 4'),
        ('Check8', 'Chăm sóc lần 5'),
        ('Check4', 'Chăm sóc kết thúc liệu trình lần 1'),
        ('Check5', 'Chăm sóc kết thúc liệu trình lần 2'),
        ('Check6', 'Chăm sóc kết thúc liệu trình lần 3'),
        ('Check7', 'Chăm sóc kết thúc liệu trình lần 4'),
        ('Check8', 'Chăm sóc kết thúc liệu trình lần 5'),
        ('Change', 'Thay băng lần 1'),
        ('Change1', 'Thay băng lần 2'),
        ('Change2', 'Thay băng lần 3'),
        ('Change3', 'Thay băng lần 4'),
        ('Change4', 'Thay băng lần 5'),
        ('Change5', 'Thay băng lần 6'),
        ('ReCheck', 'Cắt chỉ'),
        ('ReCheck1', 'Hút dịch'),
        ('ReCheck2', 'Rút ống mũi'),
        ('ReCheck3', 'Thay nẹp mũi'),
        ('ReCheck4', 'Tái khám lần 1'),
        ('ReCheck5', 'Tái khám lần 2'),
        ('ReCheck6', 'Tái khám lần 3'),
        ('ReCheck7', 'Tái khám lần 4'),
        ('ReCheck8', 'Tái khám lần 5'),
        ('ReCheck11', 'Tái khám lần 6'),
        ('ReCheck9', 'Tái khám định kì'),
        ('ReCheck10', 'Nhắc liệu trình'),
        ('Return', 'Tái khai thác KH cũ'),
        ('Sale1', 'Chăm sóc bán lần 1'),
        ('Sale2', 'Chăm sóc bán lần 2')
    ]

    name = fields.Char("Tên")
    service_id = fields.Many2many('sh.medical.health.center.service', 're_reexam_service_id', 'sh_medical_health_center_service_reexam_id', 'sh_medical_health_center_service_id', string='Service', ondelete='cascade')
    service_id_LT = fields.Many2many('sh.medical.health.center.service', 're_reexam_service_id_lt', 'sh_medical_health_center_service_reexam_id', 'sh_medical_health_center_service_id', string='Service', ondelete='cascade')
    service_id_eoc = fields.Many2many('sh.medical.health.center.service', 're_reexam_service_id_eoc', 'sh_medical_health_center_service_reexam_id', 'sh_medical_health_center_service_id', string='Service', ondelete='cascade')
    after_service_date = fields.Integer('Sau ngày (ngày)', required=True)
    type = fields.Selection(NOTE, 'Loại', required=True)
    care_mode = fields.Selection([('1', 'Cơ sở chăm sóc'), ('2', 'DVKH chăm sóc')], string='Chế độ chăm sóc', default='1')
    is_phonecall = fields.Boolean('Sinh phonecall?', default=False)
    is_print = fields.Boolean('Sinh hướng dẫn?', default=False)
    is_sms = fields.Boolean('Sinh SMS?', default=False, help="Gửi SMS nhắc lịch hẹn vào 9h sáng trước 1 ngày hẹn lịch của KH")
    script_id = fields.Many2one('crm.script.phone.call', string='Kịch bản')
    code = fields.Char('Mã cấu hình')
    type_date = fields.Selection([('m', 'Ngày KH ra viện (M)'), ('n', 'Ngày KH làm dịch vụ (N)')],
                                 string='Loại ngày sinh')

    _sql_constraints = [('unique_code', 'unique(code)', 'Mã cấu hình đã tồn tại!!.')]
    #
    # @api.onchange('script_id', 'type_date', 'after_service_date')
    # def change_code(self):
    #     str_code = ''
    #     if self.script_id:
    #         str_code += self.script_id.code
    #         self.name = self.script_id.name
    #     if self.type_date:
    #         str_code += "-" + self.type_date
    #     if self.after_service_date:
    #         str_code += str(self.after_service_date)
    #     self.code = str_code.upper()

class SHealthServiceCategory(models.Model):
    _name = 'sh.medical.health.center.service.category'
    _description = "Nhóm dịch vụ"

    _inherits = {
        'product.category': 'product_cat_id',
    }

    product_cat_id = fields.Many2one('product.category', string='Related Product Category', required=True, ondelete='cascade',
                                 help='Product-related data of the category')
    is_another_cost = fields.Boolean('Là chi phí khác', help='Những nhóm dịch vụ được tick sẽ có thể thêm các dịch vụ thuộc nhóm này tại phiếu thu.')
    # code = fields.Char("Mã", required=True)

    @api.model
    def create(self, vals):
        vals['parent_id'] = self.env.ref('shealth_all_in_one.sh_services').id
        service = super(SHealthServiceCategory, self).create(vals)
        return service

class SHealthServiceUomGuarantee(models.Model):
    _name = 'sh.medical.health.center.uom.guarantee'
    _description = "Đơn vị tính của thời gian bảo hành"

    name = fields.Char("Tên", required=True)

# Services
class SHealthServices(models.Model):
    _name = 'sh.medical.health.center.service'
    _description = "Information about the services of health center"
    _inherits = {
        'product.product': 'product_id',
    }

    _order = "default_code"

    def name_get(self):
        res = []
        for service in self:
            if self.env.context.get('only_name'):
                res.append((service.id, _('%s') % (service.name)))
            elif self.env.context.get('only_code'):
                res.append((service.id, _('%s') % (service.default_code)))
            else:
                res.append((service.id, _('[%s] %s') % (service.default_code, service.name)))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('default_code', operator, name)]
        service = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(service).name_get()

    @api.model
    def _get_euro(self):
        return self.env['res.currency.rate'].search([('rate', '=', 1)], limit=1).currency_id

    @api.model
    def _get_user_currency(self):
        currency_id = self.env['res.users'].browse(self._uid).company_id.currency_id
        return currency_id or self._get_euro()

    product_id = fields.Many2one('product.product', string='Related Product', required=True,ondelete='cascade', help='Product-related data of the services')
    diagnose = fields.Char('Chẩn đoán')
    surgical_method = fields.Char('Phương pháp phẫu thuật')
    # code = fields.Char(string='Code', size=128, help="Short code for the service")
    # institution = fields.Many2one('sh.medical.health.center', string='Health Center', required=True)
    info = fields.Text(string='Hướng dẫn sau dịch vụ')
    days_reexam = fields.Many2many('sh.medical.health.center.service.reexam', 're_reexam_service_id', 'sh_medical_health_center_service_id', 'sh_medical_health_center_service_reexam_id', string='Phonecall dịch vụ lẻ')
    days_reexam_LT = fields.Many2many('sh.medical.health.center.service.reexam', 're_reexam_service_id_lt', 'sh_medical_health_center_service_id', 'sh_medical_health_center_service_reexam_id', string='Phonecall dịch vụ liệu trình')
    days_reexam_eoc = fields.Many2many('sh.medical.health.center.service.reexam', 're_reexam_service_id_eoc', 'sh_medical_health_center_service_id', 'sh_medical_health_center_service_reexam_id', string='Phonecall kết thúc dịch vụ liệu trình')

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self._get_user_currency())

    # lab_criteria = fields.One2many('sh.medical.labtest.criteria', 'medical_type_id', string='Lab Test Cases')
    # service_department = fields.Many2one('sh.medical.health.center.ward', string='Department perform', domain="[('institution', '=', institution)]")
    institution = fields.Many2many('sh.medical.health.center', string='Cơ sở y tế', required=True)
    service_department = fields.Many2many('sh.medical.health.center.ward','service_departments_rel', string='Department perform', domain="[('institution.his_company','in',allowed_company_ids)]", hint='Select departments can be performance this service')
    # child_service = fields.One2many('sh.medical.health.center.service.childs', 'service_id', string='Extra services')
    # child_service_other = fields.Many2many('sh.medical.health.center.service', 'service_child_ids', string='Child services other', compute="_depend_child_service")

    #thong tin vat tu
    material_ids = fields.One2many('sh.medical.service.material','service_id',string="Material Information")
    #thong tin đơn thuốc mang về
    prescription_ids = fields.One2many('sh.medical.service.prescription','service_id',string="Prescription Information")

    genetic_risks = fields.Many2many('sh.medical.labtest.types', 'sh_genetic_risks_service_rel', 'patient_id', 'genetic_risk_id',
                                     string='Genetic Risks')
    # lab_type_ids = fields.Many2many('sh.medical.labtest.types', 'sh_medical_services_labtest_types_rel', 'service_id', 'labtest_type_id',string='Labtest Type', domain="[('institution', '=', institution)]")
    # imaging_type_ids = fields.Many2many('sh.medical.imaging.test.type', 'sh_medical_services_imaging_test_types_rel', 'service_id', 'imaging_type_id',string='Imaging Type', domain="[('institution', '=', institution)]")
    lab_type_ids = fields.Many2many('sh.medical.labtest.types', 'sh_medical_services_labtest_types_rel', 'service_id', 'labtest_type_id',string='Labtest Type')
    imaging_type_ids = fields.Many2many('sh.medical.imaging.test.type', 'sh_medical_services_imaging_test_types_rel', 'service_id', 'imaging_type_id', string='Imaging Type')

    # CÁC BOM
    other_bom = fields.One2many('sh.medical.product.bundle','service_id',string="Other BOM")

    # TODO: CẦN BỎ TRƯỜNG NÀY
    is_surgeries = fields.Boolean('Is Surgeries')

    surgery_type = fields.Selection([('minor', 'Tiểu phẫu'),('major', 'Đại phẫu')], 'Loại phẫu thuật')
    surgical_diagram = fields.Html('Lược đồ phẫu thuật')
    surgical_order = fields.Text('Trình tự phẫu thuật')

    anesthetist_type = fields.Selection([('te', 'Gây tê'),('tien_me', 'Tiền mê'),('me', 'Gây mê'),('tetaicho', 'Tê tại chỗ'),('boite', 'Bôi tê'),('tiemte', 'Tiêm tê'),('tetuysong', 'Tê tủy sống')], 'Phương pháp thực hiện')

    # child_service_count = fields.Integer('Child service count', compute="count_child_service")
    lab_type_count = fields.Integer('Lab type count', compute="count_lab_type")
    img_type_count = fields.Integer('Imaging type count', compute="count_img_type")

    #ma benh icd10
    pathology = fields.Many2one('sh.medical.pathology', string='Pathology')

    service_category = fields.Many2one('sh.medical.health.center.service.category', string='Nhóm dịch vụ')

    his_service_type = fields.Selection(
        [('Spa', 'Spa'), ('Laser', 'Laser'), ('Odontology', 'Nha'), ('Surgery', 'Phẫu thuật'),
         ('ChiPhi', 'Chi phí khác')], 'Loại dịch vụ')

    level_of_difficult = fields.Float('Độ khó/Level', digits=(16, 2))
    execution_time = fields.Integer('Thời gian thực hiện (Phút)')
    recovery_time = fields.Integer('Thời gian phục hồi (Ngày)')
    warranty_period = fields.Integer('Thời gian Bảo hành')
    uom_guarantee = fields.Many2one('sh.medical.health.center.uom.guarantee', string='Đơn vị (Thời gian BH)')

    kpi_point = fields.Float('Điểm KPI', digits=(16, 2))
    kpi_point_num = fields.Integer('Số lượng đạt điểm KPI',help="Số lượng lần lầm dịch vụ để đạt điểm KPI")

    note = fields.Text('Ghi chú',help="Ghi chú lại 1 số nội dung liên quan Dịch vụ hoặc chế độ Bảo hành đặc biệt, v.v. ...")

    is_no_specialty = fields.Boolean('Không cần phiếu chuyên khoa?',help="Dịch vụ không cần nhập phiếu chuyên khoa")
    is_no_phonecall = fields.Boolean('Không cần lịch tái khám?',help="Dịch vụ không nhập lịch tái khám")
    is_input_num = fields.Boolean('Cho nhập số lượng thực hiện?',help="Dịch vụ cho phép nhập số lượng thực hiện")

    # TÊN IN TRÊN CHẨN ĐOÁN ĐƠN THUỐC
    technical_name = fields.Char('Technical name')

    # GHI NHẬN MỨC TRẦN KHUYẾN MÃI CỦA DỊCH VỤ
    promotional_ceiling = fields.Char(string='Mức trần khuyến mại(%)')

    service_room = fields.Many2many('sh.medical.health.center.ot','service_rooms_rel', string='Room perform')
    exam_room = fields.Many2many('sh.medical.health.center.ot','exam_rooms_rel', string='Room examination')
    # ham dem child service
    # @api.depends('child_service')
    # def count_child_service(self):
    #     for record in self:
    #         record.child_service_count = len(record.child_service)

    def write(self, vals):
        return super(SHealthServices, self).write(vals)

    # ham dem loai xet nghiem
    @api.depends('lab_type_ids')
    def count_lab_type(self):
        for record in self:
            record.lab_type_count = len(record.lab_type_ids)

    # ham dem loai cdha
    @api.depends('imaging_type_ids')
    def count_img_type(self):
        for record in self:
            record.img_type_count = len(record.imaging_type_ids)

    # @api.onchange('lab_type_ids','imaging_type_ids','child_service')
    @api.onchange('lab_type_ids','imaging_type_ids')
    def _onchange_services_case(self):
        self.list_price = 0
        # tinh vat tu tieu hao tong
        self.material_ids = False
        marterial_service = []
        for lab_type in self.lab_type_ids:
            # tinh gia service bang tong cac lab type
            self.list_price += lab_type.list_price

            for mats in lab_type.material_ids:
                marterial_service.append((0, 0, {'product_id': mats.product_id.id,
                                              'quantity': mats.quantity,
                                              # 'institution': lab_type.institution.id,
                                              # 'department': lab_type.department.id,
                                              'uom_id': mats.uom_id.id,
                                              'note': 'Labtest'}))

        for img_type in self.imaging_type_ids:
            # tinh gia service bang tong cac lab type
            self.list_price += img_type.list_price

            for mats_img in img_type.material_ids:
                marterial_service.append((0, 0, {'product_id': mats_img.product_id.id,
                                              'quantity': mats_img.quantity,
                                              # 'institution': img_type.institution.id,
                                              # 'department': img_type.department.id,
                                              'uom_id': mats_img.uom_id.id,
                                              'note': 'Imaging'}))

        # if self.child_service:
        #     # tinh gia service bang tong cac service con
        #     for service in self.child_service:
        #         self.list_price += service.list_price * service.service_unit
        #
        #     #lay vat tu tu service con add cho service cha
        #     for child in self.child_service:
        #         print(child.name)
        #         for mats_child in child.material_ids:
        #             marterial_service.append((0, 0, {'product_id': mats_child.product_id.id,
        #                                           'quantity': (mats_child.quantity * child.service_unit),
        #                                           'institution': child.institution.id,
        #                                           'department': child.service_department.id,
        #                                           'uom_id': mats_child.uom_id.id,
        #                                           'note': 'Extra'}))

        self.update({'material_ids': marterial_service})

    @api.model
    def create(self, vals):
        vals["type"] = 'service'
        service = super(SHealthServices, self).create(vals)
        return service

    # @api.onchange('institution')
    # def _onchange_institution(self):
    #     # self.service_department = ''
    #     print("COMPANY:")
    #     print(self.env.context['allowed_company_ids'])

    # @api.onchange('service_department')
    # def _onchange_service_department(self):
    #     # self.service_department = ''
    #     print("DEP:")
    #     print(self.env.context['allowed_company_ids'])


    # @api.depends('child_service')
    # def _depend_child_service(self):
    #     for record in self:
    #         # print(record.child_service)
    #         if len(record.child_service) > 0:
    #             record.child_service_other = [(6,0,[line.service_child_ids.id for line in record.child_service if line.service_child_ids])]

    # IN THUỐC KÊ ĐƠN MANG VỀ

    def print_temp_donthuoc(self):
        return self.env.ref('shealth_all_in_one.action_report_temp_prescription_service').report_action(self)

    # IN HƯỚNG DẪN SAU DỊCH VỤ

    def print_temp_huongdan(self):
        return self.env.ref('shealth_all_in_one.action_report_temp_huongdan_service').report_action(self)

# class SHealthServiceChild(models.Model):
#     _name = 'sh.medical.health.center.service.childs'
#     _description = 'All child of the service'
#
#     service_id = fields.Many2one('sh.medical.health.center.service', string='Service child id')
#     service_child_ids = fields.Many2one('sh.medical.health.center.service', string='Service child')
#     service_unit = fields.Integer('Service unit')  # số lần sử dụng dịch vụ
#
#     default_code = fields.Char(string='Code', compute='_compute_service_childs_id')
#     name = fields.Char(string='Service name', compute='_compute_service_childs_id')
#     institution = fields.Many2one('sh.medical.health.center', string='Health Center', compute='_compute_service_childs_id')
#     service_department = fields.Many2one('sh.medical.health.center.ward', string='Department perform',compute='_compute_service_childs_id')
#     currency_id = fields.Many2one('res.currency', string='Currency',compute='_compute_service_childs_id')
#     info = fields.Text(string='Description', compute='_compute_service_childs_id')
#     list_price = fields.Float('Sale price', compute='_compute_service_childs_id')
#     is_surgeries = fields.Boolean('Is Surgeries', compute='_compute_service_childs_id')
#     # ma benh icd10
#     pathology = fields.Many2one('sh.medical.pathology', string='Pathology', compute='_compute_service_childs_id')
#
#     # thong tin vat tu
#     material_ids = fields.One2many('sh.medical.service.material', 'service_id', string="Material Information")
#
#     @api.onchange('service_child_ids')
#     def _onchange_service_child_ids(self):
#         parent_id = self.env.context.get('parent_id')
#
#         if parent_id > 0:
#             if len(self.service_id.child_service_other) > 0:
#                 return {
#                     'domain': {'service_child_ids': [('id', '!=', parent_id),
#                                                                    ('id', 'not in', self.service_id.child_service_other.ids)]}}
#             else:
#                 return {
#                     'domain': {'service_child_ids': [('id', '!=', parent_id)]}}
#         else:
#             if len(self.service_id.child_service_other) > 0:
#                 return {'domain': {'service_child_ids': [('id', 'not in', self.service_id.child_service_other.ids)]}}
#
#     @api.depends('service_child_ids')
#     def _compute_service_childs_id(self):
#         for record in self:
#             if record.service_child_ids:
#                 record.default_code = record.service_child_ids.default_code
#                 record.name = record.service_child_ids.name
#                 record.list_price = record.service_child_ids.list_price
#                 record.institution = record.service_child_ids.institution.id
#                 record.service_department = record.service_child_ids.service_department.id
#                 record.currency_id = record.service_child_ids.currency_id
#                 record.info = record.service_child_ids.info
#                 record.is_surgeries = record.service_child_ids.is_surgeries
#                 record.material_ids = record.service_child_ids.material_ids
#                 record.pathology = record.service_child_ids.pathology


class SHealthServiceMaterial(models.Model):
    _name = 'sh.medical.service.material'
    _description = 'All material of the service'

    NOTE = [
        ('Labtest', 'Material of Labtest'),
        ('Imaging', 'Material of Imaging'),
        ('Surgery', 'Material of Surgery'),
        ('Specialty', 'Material of Specialty Service'),
        ('Inpatient', 'Material of Inpatient'),
        # ('Extra', 'Material of Extra Service'),
    ]

    sequence = fields.Integer('Sequence', default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự
    service_id = fields.Many2one('sh.medical.health.center.service', string='Service')
    product_id = fields.Many2one('sh.medical.medicines', string='Product', required=True, domain=lambda self:[('categ_id','child_of',self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    # medicine_id = fields.Many2one('sh.medical.medicines', string='Supplies', required=True, domain="[('medicament_type', '=', 'Supplies')]")
    quantity = fields.Float('Quantity', digits='Product Unit of Measure', default=1)  # số lượng sử dụng vật tư
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    note = fields.Selection(NOTE, 'Material note')

    # institution = fields.Many2one('sh.medical.health.center', string='Health Center', required=True)
    # department = fields.Many2one('sh.medical.health.center.ward', string='Department', required=True)

    @api.onchange('product_id')
    def _change_product_id(self):
        self.uom_id = self.product_id.uom_id

        return {'domain': {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.product_id.uom_id.category_id:
            self.uom_id = self.product_id.uom_id
            raise Warning(_('The Service Unit of Measure and the Material Unit of Measure must be in the same category.'))

class SHealthServicePrescription(models.Model):
    _name = 'sh.medical.service.prescription'
    _description = 'Prescription of the service'

    DURATION_UNIT = [
        ('Minutes', 'Minutes'),
        ('Hours', 'Hours'),
        ('Days', 'Days'),
        ('Months', 'Months'),
        ('Years', 'Years'),
        ('Indefinite', 'Indefinite'),
    ]

    sequence = fields.Integer('Sequence', default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự
    service_id = fields.Many2one('sh.medical.health.center.service', string='Service')
    product_id = fields.Many2one('sh.medical.medicines', string='Medicine', required=True, domain=lambda self:[('categ_id','child_of',self.env.ref('shealth_all_in_one.sh_medicines').id)])
    qty = fields.Float('Quantity', digits='Product Unit of Measure',default=1)  # số lượng
    dose = fields.Float('Dose', digits='Product Unit of Measure')  # liều dùng
    dose_unit = fields.Many2one('uom.uom', 'Unit of Measure')
    common_dosage = fields.Many2one('sh.medical.dosage', string='Frequency', help="Common / standard dosage frequency for this medicines")
    duration = fields.Integer(string='Treatment duration')
    duration_period = fields.Selection(DURATION_UNIT, string='Treatment period',
                                       help="Period that the patient must take the medication. in minutes, hours, days, months, years or indefinately",
                                       index=True)

    note = fields.Text('Note')
    is_buy_out = fields.Boolean('Mua ngoài', default=False)

    @api.onchange('product_id')
    def _change_product_id(self):
        self.dose_unit = self.product_id.uom_id

    @api.onchange('dose_unit')
    def _change_dose_unit(self):
        if self.dose_unit.category_id != self.product_id.uom_id.category_id:
            self.dose_unit = self.product_id.uom_id
            raise Warning(_('The Service Unit of Measure and the Material Unit of Measure must be in the same category.'))