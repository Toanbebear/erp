import datetime

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class SelectServiceLine(models.TransientModel):
    _name = 'crm.select.service.line'
    _description = 'Select Service Line'

    booking_id = fields.Many2one('crm.lead', string='Booking')
    select_service_id = fields.Many2one('crm.select.service', string='Select service')
    teeth_ids = fields.Many2many('sh.medical.teeth', string='Mã răng')
    currency_id = fields.Many2one(related='booking_id.currency_id')
    amount = fields.Monetary('Số tiền')
    uom_price = fields.Float('cm2/cc/unit/...')
    quantity = fields.Integer('Số lượng', default=1)
    exam_room_id = fields.Many2one('sh.medical.health.center.ot', string='Exam room')

    # def get_domain_crm_line(self):
    #     # print('hello', self.env.booking_id.booking_date)
    #     if not self.env.user.has_group('base.group_system'):
    #         return "['&', '&', ('exam_room_ids','in',parent.exam_room_id),('crm_id','=',booking_id), '|', ('stage', '=', 'new'),'&',('odontology','=',True),('stage', 'in', ['new', 'done'])]"
    #     else:
    #         return "[('crm_id','=',booking_id)]"

    # crm_line_id = fields.Many2one('crm.line', string='Services', domain=lambda self: self.get_domain_crm_line())
    crm_line_id = fields.Many2one('crm.line', string='Services')

    is_input_num = fields.Boolean(default=False, help="Cho phép nhập trường đơn vị xử lý")
    dentistry = fields.Boolean('Nha khoa')

    @api.onchange('crm_line_id', 'amount', 'uom_price')
    def onchange_validate_amount(self):
        if self.crm_line_id and self.amount:
            if self.crm_line_id.total < self.amount:
                raise ValidationError('Tổng tiền của lần làm dịch vụ này lớn hơn tổng tiền phải thu của khách')
            if self.crm_line_id.uom_price < self.uom_price:
                raise ValidationError(
                    'Đơn vị xử lý cho lần làm này vượt quá đơn vị xử lý khách hàng đăng ký trên Booking')

    @api.constrains('crm_line_id', 'amount', 'uom_price')
    def validate_amount(self):
        for record in self:
            if record.crm_line_id and record.amount and record.uom_price:
                if record.crm_line_id.total < record.amount:
                    raise ValidationError('Tổng tiền của lần làm dịch vụ này lớn hơn tổng tiền phải thu của khách')
                if record.crm_line_id.uom_price < record.uom_price:
                    raise ValidationError(
                        'Đơn vị xử lý cho lần làm này vượt quá đơn vị xử lý khách hàng đăng ký trên Booking')

    @api.onchange('exam_room_id', 'booking_id', 'select_service_id.select_line_ids')
    def get_line_service(self):
        if self.booking_id.booking_date >= datetime.datetime.strptime('2021/11/01 00:00:01', '%Y/%m/%d %H:%M:%S'):
            if self.dentistry:
                # line_ids = self.env['crm.line'].search([('stage', 'in', ['new', 'done']), ('odontology', '=', True),
                #                                         ('exam_room_ids', 'in', self.exam_room_id.id),
                #                                         ('crm_id', '=', self.booking_id.id)])
                line_ids = self.env['crm.line'].search([('stage', 'in', ['new', 'done']),
                                                        ('exam_room_ids', 'in', self.exam_room_id.id),
                                                        ('crm_id', '=', self.booking_id.id),
                                                        ('id', 'not in', self.select_service_id.chosen_line_ids.ids)])
                return {'domain': {'crm_line_id': [('id', 'in', line_ids.ids)]}}
            else:
                # line_ids = self.env['crm.line'].search([('stage', '=', 'new'), ('odontology', '=', False),
                #                                         ('exam_room_ids', 'in', self.exam_room_id.id),
                #                                         ('crm_id', '=', self.booking_id.id)])
                line_ids = self.env['crm.line'].search([('stage', '=', 'new'),
                                                        ('exam_room_ids', 'in', self.exam_room_id.id),
                                                        ('crm_id', '=', self.booking_id.id),
                                                        ('id', 'not in', self.select_service_id.chosen_line_ids.ids)])
                return {'domain': {'crm_line_id': [('id', 'in', line_ids.ids)]}}
        else:
            line_ids = self.env['crm.line'].search(
                [('crm_id', '=', self.booking_id.id), ('stage', 'not in', ['processing', 'cancel']),
                 ('exam_room_ids', 'in', self.exam_room_id.id), ('id', 'not in', self.select_service_id.chosen_line_ids.ids)])
            return {'domain': {'crm_line_id': [('id', 'in', line_ids.ids)]}}

    @api.onchange('crm_line_id')
    def onchange_crm_line(self):
        if self.crm_line_id:
            self.uom_price = self.crm_line_id.uom_price
            self.is_input_num = self.crm_line_id.is_input_num
            if self.crm_line_id.odontology:
                crm_line_ids = self.env['crm.line'].search(
                    [('crm_id', '=', self.booking_id.id), ('stage', 'in', ['new', 'done', 'processing']),
                     ('service_id', 'in', self.crm_line_id.mapped('service_id').ids)])
                self.amount = ((self.crm_line_id.total / (
                        self.crm_line_id.quantity * self.crm_line_id.uom_price)) * self.uom_price) if self.crm_line_id.total else 0
                return {'domain': {'teeth_ids': [('id', '=', crm_line_ids.mapped('teeth_ids').ids)]}}
            else:
                self.amount = ((self.crm_line_id.total / (
                        self.crm_line_id.quantity * self.crm_line_id.uom_price)) * self.uom_price) if self.crm_line_id.total else 0

    # @api.constrains('crm_line_id', 'amount', 'uom_price')
    # def validate_amount_and_uom_price(self):
    #     for record in self:
    #         if record.crm_line_id.odontology:
    #             crm_line_ids = record.env['crm.line'].search(
    #                 [('crm_id', '=', record.booking_id.id), ('stage', 'not in', ['cancel']),
    #                  ('service_id', 'in', record.crm_line_id.mapped('service_id').ids)])
    #             if record.amount > sum(crm_line_ids.mapped('total')):
    #                 raise ValidationError('Số tiền nhập lớn hơn số tiền thực tế khách phải đóng')
    #         if record.crm_line_id.uom_price < record.uom_price:
    #             raise ValidationError(
    #                 'Đơn vị xử lý cho lần làm này vượt quá đơn vị xử lý khách hàng đăng ký trên Booking')

    @api.onchange('teeth_ids')
    def get_service(self):
        self.uom_price = 1
        if self.teeth_ids:
            self.uom_price = len(self.teeth_ids)


class CRMSelectService(models.TransientModel):
    _inherit = 'crm.select.service'

    institution = fields.Many2one('sh.medical.health.center', string='Institution',
                                  domain="[('id','in',institution_ids)]")
    exam_room_id = fields.Many2one('sh.medical.health.center.ot', string='Exam room',
                                   domain="[('department.type','=','Examination'),('institution','=',institution),('related_department', '!=', False)]")

    institution_ids = fields.Many2many('sh.medical.health.center', string='List institution',
                                       compute='set_institutions', store=True)

    dentistry = fields.Boolean('Dentistry')
    select_line_ids = fields.One2many('crm.select.service.line', 'select_service_id', string='Select line')
    chosen_line_ids = fields.Many2many('crm.line', help="Line đã chọn")
    doctor_order = fields.Many2one('sh.medical.physician', string='Trưởng ekip phẫu thuật', domain="[('is_doctor_order','=', True)]", help="Bác sĩ được khách hàng yêu cầu")
    flag_surgery = fields.Boolean('Phòng phẫu thuật?')

    @api.onchange('exam_room_id')
    def check_flag_surgery(self):
        if self.exam_room_id and self.exam_room_id.related_department.type == 'Surgery':
            self.flag_surgery = True
        else:
            self.flag_surgery = False

    # Lấy ra danh sách các line đã chọn để tránh việc 1 line được chọn 2 lần
    @api.onchange('select_line_ids', 'booking_id')
    def get_line_chose(self):
        self.chosen_line_ids = False
        if self.select_line_ids and len(self.select_line_ids) != 0:
            self.chosen_line_ids = [(6, 0, self.select_line_ids.mapped('crm_line_id').ids)]

    @api.depends('booking_id', 'exam_room_id')
    def _check_booking(self):
        for record in self:
            record.check_booking_date = True
            if (record.booking_id.booking_date <= datetime.datetime.strptime('2021/11/3 16:59:59',
                                                                             '%Y/%m/%d %H:%M:%S')) and (
                    record.exam_room_id.related_department.type == 'Odontology'):
                record.check_booking_date = False

    def set_total_order(self):
        total_amount = 0
        for rec in self:
            if rec.select_line_ids:
                for record in rec.select_line_ids:
                    total_amount += record.amount
        return total_amount

    @api.onchange('exam_room_id')
    def onchange_exam_room_id(self):
        if self.exam_room_id:
            self.select_line_ids = False
            self.dentistry = False
            if self.exam_room_id.related_department.type == 'Odontology':
                self.dentistry = True

    @api.onchange('institution')
    def reset_exam(self):
        self.exam_room_id = False

    @api.onchange('exam_room_id')
    def reset_service(self):
        self.crm_line_ids = False

    @api.depends('company_ids')
    def set_institutions(self):
        for rec in self:
            if rec.booking_id.type_brand == 'hospital':
                list_institution = []
                if rec.company_ids:
                    for company in rec.company_ids._origin.ids:
                        ins = self.env['sh.medical.health.center'].sudo().search([('his_company', '=', company)])
                        list_institution.append(ins.id)
                    rec.institution_ids = [(6, 0, list_institution)]
            else:
                rec.institution_ids = False
