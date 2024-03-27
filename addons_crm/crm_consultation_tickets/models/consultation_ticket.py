from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

# Nguồn biết đến
KNOW_SOURCE = [
    ('web', 'Website/Facebook'),
    ('hotline', 'Tư vấn Hotline'),
    ('voucher', 'Voucher trải nghiệm'),
    ('ctv', 'Cộng tác viên'),
    ('lcd', 'LCD/Frame/Poster'),
    ('brand', 'Đi ngang chi nhánh'),
    ('friend', 'Người thân/Bạn bè'),
    ('seminor', 'Hội thảo'),
    ('business', 'Nhân viên kinh doanh'),
    ('qc', 'Quảng các TV'),
    ('other', 'Khác')
]


class ConsultationDetailTicket(models.Model):
    _name = 'consultation.detail.ticket'
    _description = 'Consultation Detail Ticket'

    consultation_ticket_id = fields.Many2one('consultation.ticket')
    booking_id = fields.Many2one('crm.lead', string='Mã Booking', related="consultation_ticket_id.booking_id")
    product_id = fields.Many2one('product.product', string='Sản phẩm')
    desire = fields.Text('Mong muốn')
    health_status = fields.Text('Tình trạng')
    level_of_improvement = fields.Text('Mức độ cải thiện')
    schedule = fields.Text('Lịch trình')
    warranty = fields.Text('Chế độ bảo hành')
    product_for_home_use = fields.Text('Sản phẩm sử dụng tại nhà')
    note = fields.Text('Ghi chú')
    confirm_service = fields.Boolean('Xác nhận')
    service_id = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ')
    consultation = fields.Text('Tư vấn')

    @api.onchange('confirm_service', 'service_id', 'consultation_ticket_id')
    def get_warning(self):
        if self.confirm_service and self.service_id and not self.consultation_ticket_id.source_id:
            raise ValidationError('Vui lòng chọn giá trị NGUỒN GHI NHẬN')

    @api.onchange('booking_id')
    def get_list_service(self):
        list_company = self.env['res.company']
        if self.booking_id.company_id:
            list_company += self.booking_id.company_id
            if self.booking_id.company2_id:
                list_company += self.booking_id.company2_id
        institution = self.env['sh.medical.health.center'].search([('his_company', 'in', list_company.ids)])
        return {'domain': {'service_id': [('id', 'in', self.env['sh.medical.health.center.service'].sudo().search(
            [('institution', 'in', institution.ids)]).ids)]}}


class ConsultationTicket(models.Model):
    _name = 'consultation.ticket'
    _description = 'Consultation Ticket'

    name = fields.Char('Mã phiếu')
    company_id = fields.Many2one('res.company', string='Chi nhánh', default=lambda self: self.env.user.company_id.id)
    booking_id = fields.Many2one('crm.lead', string='Booking', domain="[('type','=','opportunity')]")
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    allergy_history = fields.Text(string='Tiền sử dị ứng')
    name_customer = fields.Char(string='Tên khách hàng')
    code_customer = fields.Char(string='Mã khách hàng')
    gender_customer = fields.Selection([('male', 'Nam'), ('female', 'Nữ'), ('transguy', 'Transguy'),
                                        ('transgirl', 'Transgirl'), ('other', 'Khác')], string='Giới tính')
    birth_date_customer = fields.Char('Ngày/tháng/năm sinh')
    passport_customer = fields.Char('Số CMTND/CCCD/Hộ chiếu')
    passport_date_customer = fields.Date('Ngày cấp')
    address_customer = fields.Char('Nơi cư trú hiện tại')
    phone_customer = fields.Char('Số điện thoại')
    emergency_phone_customer = fields.Char('Số điện thoại khẩn cấp')
    email_customer = fields.Char('Email')
    know_source = fields.Selection(KNOW_SOURCE, string='Nguồn biết đến')
    consultation_doctor = fields.Many2one('res.partner', string='Bác sĩ tư vấn')
    consultation_reception = fields.Many2one('res.users', string='Lễ tân tư vấn', default=lambda self: self.env.user)
    consultation_detail_ticket_ids = fields.One2many('consultation.detail.ticket', 'consultation_ticket_id',
                                                     string='Thông tin tư vấn')
    source_id = fields.Many2one('utm.source', 'Nguồn ghi nhận')

    sh_medical_physician_id = fields.Many2one('sh.medical.physician', string='Bác sĩ tư vấn')

    def open_and_print_consultation_ticket(self):
        return self.env.ref('crm_consultation_tickets.action_print_consultation_ticket').report_action(self)

    # Lấy danh sách các bác sĩ ở chi nhánh này
    @api.onchange('company_id')
    def get_sh_medical_physician_id(self):
        if self.company_id:
            return {'domain': {'sh_medical_physician_id': [('id', 'in', self.env['sh.medical.physician'].sudo().search(
                [('company_id', '=', self.company_id.id)]).ids)]}}

    # Lấy danh sách các dịch vụ từ BK lên phiếu tư vấn
    @api.onchange('booking_id')
    def get_consultation_detail_ticket(self):
        if self.booking_id and self.booking_id.crm_line_ids:
            for record in self.booking_id.crm_line_ids:
                if (record.stage == 'new') or (record.odontology and (record.stage in ['new', 'done'])):
                    self.consultation_detail_ticket_ids = [(0, 0, {
                        'service_id': record.service_id.id
                    })]

    @api.model
    def create(self, vals):
        res = super(ConsultationTicket, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('consultation.ticket')
        if res.consultation_detail_ticket_ids:
            # Lấy ra danh sách dịch vụ ở Line BK có trạng thái new
            line_booking_new_ids = self.env['crm.line'].search(
                [('stage', '=', 'new'), ('crm_id', '=', res.booking_id.id)])
            list_service_in_crm_line = line_booking_new_ids.mapped('service_id')
            for record in res.consultation_detail_ticket_ids:
                if record.desire:
                    self.env['pain.point.and.desires'].sudo().create({
                        'type': 'desires',
                        'partner_id': res.partner_id.id,
                        'name': res.name + ': ' + record.service_id.name + ': ' + record.desire
                    })
                if record.health_status:
                    self.env['pain.point.and.desires'].sudo().create({
                        'type': 'pain_point',
                        'partner_id': res.partner_id.id,
                        'name': res.name + ': ' + record.service_id.name + ': ' + record.health_status
                    })
                if record.confirm_service and (record.service_id not in list_service_in_crm_line):
                    if res.source_id:
                        self.env['crm.line'].create({
                            'product_id': record.service_id.product_id.id,
                            'service_id': record.service_id.id,
                            'quantity': 1,
                            'price_list_id': res.booking_id.price_list_id.id,
                            'unit_price': self.env['product.pricelist.item'].search(
                                [('pricelist_id', '=', res.booking_id.price_list_id.id),
                                 ('product_id', '=', record.service_id.product_id.id)]).fixed_price,
                            'crm_id': res.booking_id.id,
                            'company_id': res.booking_id.company_id.id,
                            'source_extend_id': res.source_id.id,
                            'line_booking_date': fields.datetime.now(),
                            'status_cus_come': 'come',
                        })
                    else:
                        raise ValidationError(
                            'Bạn cần chọn nguồn mở rộng(Nguồn ghi nhận) cho dịch vụ khai thác thêm từ phiếu tư vấn này!!!')
        return res

    @api.onchange('booking_id')
    def get_info_partner(self):
        if self.booking_id:
            if self.booking_id.partner_id:
                partner = self.booking_id.partner_id
                address = []
                if partner.street:
                    address.append(partner.street)
                if partner.district_id:
                    address.append(partner.district_id.name)
                if partner.state_id:
                    address.append(partner.state_id.name)
                if partner.country_id:
                    address.append(partner.country_id.name)
                self.partner_id = partner.id
                self.allergy_history = partner.allergy_history if partner.allergy_history else False
                self.name_customer = partner.name
                self.code_customer = partner.code_customer
                self.gender_customer = partner.gender
                self.birth_date_customer = partner.birth_date or partner.year_of_birth
                self.passport_customer = partner.pass_port
                self.passport_date_customer = partner.pass_port_date
                self.address_customer = '.'.join(address)
                self.phone_customer = partner.phone
                self.email_customer = partner.email
