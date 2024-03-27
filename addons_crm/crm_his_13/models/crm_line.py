from odoo import fields, models, api
from odoo.exceptions import ValidationError


class CrmLine(models.Model):
    _inherit = 'crm.line'

    institution = fields.Many2one('sh.medical.health.center', string='Institution', tracking=True)
    institution_shared = fields.Many2many('sh.medical.health.center', 'institution_shared_line_ref', 'institutions',
                                          'line', string='Institution shared', compute='get_institution', store=True,
                                          tracking=True)
    service_id = fields.Many2one('sh.medical.health.center.service', string='Service', tracking=True)
    his_service_type = fields.Selection(related='service_id.his_service_type', store=True)
    exam_room_ids = fields.Many2many('sh.medical.health.center.ot', 'exam_room_line_ref', 'exam_room', 'line',
                                     string='Exam room', compute='set_service', store=True, tracking=True)
    odontology = fields.Boolean('Odontology', compute='set_odontology', store=True, tracking=True)
    come_number = fields.Integer('Come number', compute='come_number_compute', store=True, tracking=True)
    teeth_ids = fields.Many2many('sh.medical.teeth', 'crm_line_teeth_ref', 'line', 'teeth',
                                 string='Mã răng', tracking=True)
    is_treatment = fields.Boolean('Liệu trình?', tracking=True)
    is_input_num = fields.Boolean(default=False, help="Cho phép nhập trường đơn vị xử lý",
                                  related="service_id.is_input_num", tracking=True)
    quantity_charged = fields.Integer('Số lượng tính giá', compute='get_quantity_charged', readonly=True, store=True,
                                      tracking=True)

    warranty_period = fields.Integer(related='service_id.warranty_period')
    uom_warranty = fields.Many2one(related='service_id.uom_guarantee')
    note_warranty = fields.Text(related='service_id.note', string='Ghi chú bảo hành')
    allow_adjust_unit_price = fields.Boolean('Cho phép điều chỉnh đơn giá',
                                             related='service_id.allow_adjust_unit_price')

    # @api.constrains('type_pricelist', 'initial_product_id')
    # def constraint_line_guarantee(self):
    #     """
    #     Line dịch vụ có bảng giá bảo hành bắt buộc phải có dịch vụ ban đầu
    #     """
    #     for record in self:
    #         if record.type_pricelist == 'guarantee' and not record.initial_product_id:
    #             raise ValidationError('Thiếu dịch vụ ban đầu cho dịch vụ bảo hành này \n'
    #                                   ' Để thêm dịch vụ bảo hành, bạn cần sử dụng chức năng THÊM DỊCH VỤ BẢO HÀNH tại Booking BH')

    @api.onchange('service_id')
    def check_create_service(self):
        """
        Không phải người tạo sẽ không thể thay đổi dịch vụ
        """
        if self.service_id and self.create_uid and (self.env.user != self.create_uid):
            raise ValidationError('Chỉ người tạo mới có quyền đổi dịch vụ \n'
                                  'Nếu KH muốn đổi sang dịch vụ mới bạn có thể tạo 1 line dịch vụ mới và hủy những line dịch vụ KH không muốn làm')

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = ['|', ('name', operator, name), ('his_service_type', operator, name)]
    #     partner_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
    #     return self.browse(partner_id).name_get()

    @api.depends('quantity', 'uom_price')
    def get_quantity_charged(self):
        for rec in self:
            rec.quantity_charged = rec.quantity * rec.uom_price

    @api.onchange('teeth_ids')
    def get_quantity_odontology(self):
        self.uom_price = 1
        if self.teeth_ids:
            self.uom_price = len(self.teeth_ids)

    @api.onchange('uom_price', 'teeth_ids')
    def validate_uom_price_teeth_ids(self):
        if self.teeth_ids:
            if len(self.teeth_ids) != self.uom_price:
                raise ValidationError('Đơn vị xử lý không hợp lệ với số lượng răng đăng ký!!!')

    @api.depends('sale_order_line_id', 'crm_id', 'service_id')
    def come_number_compute(self):
        for record in self:
            if record.sale_order_line_id and record.crm_id and record.service_id:
                walkin = self.env['sh.medical.appointment.register.walkin'].search(
                    [('booking_id', '=', record.crm_id.id), ('service', 'in', [record.service_id.id])])
                record.come_number = len(walkin)

    @api.depends('service_id')
    def set_odontology(self):
        for rec in self:
            rec.odontology = False
            if rec.service_id.his_service_type == 'Odontology':
                rec.odontology = True

    @api.depends('company_id', 'company_shared')
    def get_institution(self):
        for rec in self:
            rec.institution_shared = False
            if rec.crm_id.type_brand == 'hospital':
                if rec.company_id and rec.company_shared:
                    list_company = rec.company_shared._origin.ids
                    list_company.append(rec.company_id.id)
                    list_institution = []
                    for i in list_company:
                        institution = self.env['sh.medical.health.center'].sudo().search([('his_company', '=', i)])
                        if institution:
                            list_institution.append(institution.id)
                    rec.institution_shared = [(6, 0, list_institution)]

                elif rec.company_id:
                    institution = self.env['sh.medical.health.center'].sudo().search(
                        [('his_company', '=', rec.company_id.id)])
                    if institution:
                        rec.institution_shared = [(6, 0, [institution.id])]

    @api.onchange('service_id', 'odontology', 'quantity')
    def get_product_hospital(self):
        self.is_treatment = False
        if self.service_id:
            self.product_id = self.service_id.product_id.id
            if (self.service_id.days_reexam_LT and self.odontology) or (self.quantity > 1):
                self.is_treatment = True

    @api.onchange('price_list_id')
    def get_service_ids(self):
        product_ids = self.env['product.pricelist.item'].sudo().search(
            [('pricelist_id', '=', self.price_list_id.id)]).mapped('product_id')
        service_ids = self.env['sh.medical.health.center.service'].sudo().search(
            [('product_id', 'in', product_ids.ids)])
        return {'domain': {'service_id': [('id', 'in', service_ids.ids)]}}

    @api.depends('service_id', 'institution_shared')
    def set_service(self):
        for rec in self:
            rec.exam_room_ids = False
            if rec.service_id and rec.institution_shared:
                list_room = []
                for i in rec.service_id.exam_room:
                    if i.institution in rec.institution_shared._origin:
                        list_room.append(i.id)
                rec.exam_room_ids = [(6, 0, list_room)]

    @api.model
    def create(self, vals):
        res = super(CrmLine, self).create(vals)
        if res.product_id:
            service = self.env['sh.medical.health.center.service'].search([('product_id', '=', res.product_id.id)])
            if service:
                res.service_id = service.id
        if res.crm_id.booking_date:
            res.line_booking_date = res.crm_id.booking_date
        return res
