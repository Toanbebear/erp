import json
from datetime import datetime, date, timedelta
import requests
import pytz
from dateutil.relativedelta import relativedelta
from odoo import fields, api, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.translate import _


class CRMFamilyInfo(models.Model):
    _name = 'crm.family.info'
    _description = 'CRM Family Info'

    crm_id = fields.Many2one('crm.lead', string="CRM", invisible=1)
    member_name = fields.Char(string='Name')
    type_relation_id = fields.Many2one('type.relative', string='Type relation')
    phone = fields.Char(string='Phone')
    partner_id = fields.Many2one('res.partner', string='Partner', compute='get_partner_id', store=True)
    address = fields.Char(string='Địa chỉ')

    @api.depends('phone')
    def get_partner_id(self):
        for record in self:
            if record.phone:
                partner = self.env['res.partner'].search([('phone', '=', record.phone)])
                if partner:
                    record.partner_id = partner.id
                    record.member_name = partner.name

    @api.model
    def create(self, vals_list):
        res = super(CRMFamilyInfo, self).create(vals_list)
        if res.crm_id.type == 'opportunity' and res.phone:
            partner = self.env['res.partner'].search([('phone', '=', res.phone)])
            if partner:
                res.partner_id = partner.id
                res.member_name = partner.name
            else:
                res.partner_id = False
            res.crm_id.partner_id.relation_ids.create({
                'partner_id': res.crm_id.partner_id.id,
                'partner_relative_name': res.member_name,
                'phone': res.phone,
                'type_relative_id': res.type_relation_id.id
            })
        else:
            partner = self.env['res.partner'].search([('phone', '=', res.phone)])
            if partner:
                res.partner_id = partner.id
                res.member_name = partner.name
            else:
                res.partner_id = False
        return res

    def write(self, vals):
        res = super(CRMFamilyInfo, self).write(vals)
        for record in self:
            if vals.get('phone'):
                partner = self.env['res.partner'].search([('phone', '=', record.phone)])
                if partner:
                    record.partner_id = partner.id
                    record.member_name = partner.name
                else:
                    if vals.get('member_name'):
                        record.member_name = record.member_name
                    record.partner_id = False
        return res


class CRM(models.Model):
    _inherit = 'crm.lead'

    # infomation customer

    name = fields.Char('Opportunity', required=True, index=True, tracking=True)
    birth_date = fields.Date('Birth date', tracking=True)
    year_of_birth = fields.Char('Year of birth', tracking=True)
    age = fields.Integer('Age', tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('transguy', 'Transguy'),
                               ('transgirl', 'Transgirl'), ('other', 'Other')], string='Gender', tracking=True)
    pass_port = fields.Char('Pass port', tracking=True)
    pass_port_date = fields.Date('Pass port Date', tracking=True)
    pass_port_issue_by = fields.Char('Pass port Issue by', tracking=True)
    pass_port_address = fields.Text('Permanent address', tracking=True)
    overseas_vietnamese = fields.Selection(
        [('no', 'No'), ('marketing', 'Marketing - Việt kiều'), ('branch', 'Chi nhánh - Việt kiều')],
        string='Overseas Vietnamese', default='no', tracking=True)
    district_id = fields.Many2one('res.country.district', string='District', tracking=True)
    career = fields.Char('Nghề nghiệp')

    # general

    create_on = fields.Datetime('Create on', default=lambda self: fields.Datetime.now())
    create_by = fields.Many2one('res.users', string='Create by', default=lambda self: self.env.user)
    department_id = fields.Many2one('hr.department', string='Business unit', tracking=True, compute='set_department',
                                    store=True)
    create_by_department = fields.Char('Phòng ban người tạo', related='department_id.complete_name', store=True)
    assign_time = fields.Datetime('Assign time', tracking=True, default=fields.Datetime.now())

    assign_person = fields.Many2one('res.users', string='Assigned person', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', tracking=True, related='price_list_id.currency_id')
    special_note = fields.Text('Special note', tracking=True, help="Dùng để nhập lý do hủy Booking")
    product_ctg_ids = fields.Many2many('product.category', 'product_ctg_crm_ref', 'crm_ids', 'product_ctg_ids',
                                       string='Product category', tracking=True)
    crm_line_ids = fields.One2many('crm.line', 'crm_id', string='Line service', tracking=True)
    facebook_acc = fields.Char('Facebook account', tracking=True)
    send_info_facebook = fields.Selection([('not_send', "Chưa gửi"), ('sent', 'Đã gửi')],
                                          string='Gửi thông tin Facebook', tracking=True)
    zalo_acc = fields.Char('Zalo account', tracking=True)
    send_info_zalo = fields.Selection(
        [('no_acc', "Khách hàng chưa có Zalo"), ('not_response', "Đã gửi - Chưa phản hồi"),
         ('sent', 'Đã gửi - Đã phản hồi')], string='Gửi thông tin Zalo', tracking=True)
    fam_ids = fields.One2many('crm.family.info', 'crm_id', string='Family', help='Family Information')
    type_crm_id = fields.Many2one('crm.type', string='Type record',
                                  domain='[("phone_call","=",False),("type_crm","=",type)]')
    brand_id = fields.Many2one('res.brand', string='Brand', store=True, tracking=True)
    price_list_id = fields.Many2one('product.pricelist', string='Price list', tracking=True,
                                    domain="[('type','=','service'),('brand_id','=',brand_id)]")
    category_source_id = fields.Many2one('crm.category.source', string='Category source', tracking=True)
    # source_id = fields.Many2one(domain="[('category_id','=',category_source_id), ('original_source', '=', True)]",
    #                             tracking=True)
    source_id = fields.Many2one(domain="[('original_source', '=', True)]", tracking=True)
    is_clone = fields.Boolean('Lead Clone', store=True)

    @api.onchange('source_id')
    def onchange_source(self):
        if self.source_id:
            self.category_source_id = self.source_id.category_id.id if self.source_id.category_id else False

    original_source_id = fields.Many2one('utm.source', string='Nguồn ban đầu')
    # re_exploited_source_id = fields.Many2one('utm.source', domain="[('type_source', '=', 're_exploited')]",
    #                                          tracking=True, string='Nguồn tái khai thác')
    work_online = fields.Selection([('no', 'No'), ('yes', 'Yes')], string='Work Online', tracking=True)
    note = fields.Text('Ghi chú', tracking=True)
    customer_classification = fields.Selection(
        [('5', 'Khách hàng V.I.P'), ('4', 'Đặc biệt'), ('3', 'Quan tâm hơn'), ('2', 'Quan tâm'), ('1', 'Bình thường')],
        string='Phân loại khách hàng', default='1', tracking=True)
    # new_customer = fields.Boolean(string='Khách hàng mới', compute='check_new_customer', store=True)

    # booking
    customer_come = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Customer come', tracking=True)

    def toggle_switch(self):
        if self.customer_come == 'yes':
            self.customer_come = 'no'
        else:
            self.customer_come = 'yes'

    online_counseling = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Online Counseling', tracking=True)
    shuttle_bus = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Xe đưa đón', tracking=True)
    lead_id = fields.Many2one('crm.lead', string='Lead/Booking', tracking=True)
    booking_date = fields.Datetime('Booking date', default=fields.Datetime.now(), tracking=True)
    payment_ids = fields.One2many('account.payment', 'crm_id', string='Payment')
    check_paid = fields.Boolean('Check paid')
    amount_total = fields.Monetary('Total', compute='set_total', group_operator="sum", store=True)
    amount_paid = fields.Monetary('Paid', compute='set_paid_booking', group_operator="sum", store=True)
    amount_used = fields.Monetary('Used', compute='set_used_booking', group_operator="sum", store=True)
    amount_remain = fields.Monetary('Remain', compute='set_amount_remain', group_operator="sum", store=True)
    total_amount_due = fields.Monetary('Due', compute='set_total_amount_due', group_operator="sum")
    discount_review_ids = fields.One2many('crm.discount.review', 'booking_id', string='Deep discounts')
    code_customer = fields.Char('Code customer', related='partner_id.code_customer', store=True)
    wallet_id = fields.Many2one('partner.wallet', string='Wallet')
    type_brand = fields.Selection([('hospital', 'Hospital'), ('academy', 'Academy')], string='Type brand',
                                  related='brand_id.type', store=True)
    order_ids = fields.One2many('sale.order', 'booking_id', string='Orders')
    history_discount_ids = fields.One2many('history.discount', 'crm_id', string='History discount')
    # check_won = fields.Boolean('Check won', compute='_get_day_effect_and_expire')
    code_booking = fields.Char('Mã booking tương ứng')  # Todo Bỏ
    prg_ids = fields.Many2many('crm.discount.program', 'crm_lead_prg_ref', 'prg_ids', 'crm_lead_ids',
                               string='Discount program')

    # lead
    booking_ids = fields.One2many('crm.lead', 'lead_id', string='Booking', tracking=True)
    re_open = fields.Boolean('Re-open', default=False)
    check_booking = fields.Boolean('Check booking', compute='set_check_booking', store=True)
    lead_insight = fields.Boolean('Lead insight ?')
    # inherit field
    team_id = fields.Many2one(default=False, domain="[('company_id', '=', company_id)]")
    stage_id = fields.Many2one(domain="[('crm_type_id', 'in',type_crm_id)]", default=False, tracking=True)
    country_id = fields.Many2one(default=241)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id,
                                 tracking=True)
    company2_id = fields.Many2many('res.company', 'company_crm_share_ref', 'crm', 'company', string='Company shared',
                                   tracking=True)
    type_data = fields.Selection([('old', 'Old'), ('new', 'New')], string='Type data')
    arrival_date = fields.Datetime('Ngày đến cửa')
    type_price_list = fields.Selection('Type', related='price_list_id.type', store=True)
    number_of_booking_date_changes = fields.Integer('Number of Booking date changes')
    effect = fields.Selection([('not_valid', 'Chưa hiệu lực'), ('effect', 'Hiệu lực'), ('expire', 'Hết hiệu lực')],
                              string='Effect', help="Khoảng thời gian tồn tại của Booking", default='not_valid',
                              tracking=True)
    number_of_effective_day_1 = fields.Integer('Number of effective day (A)', help="Booking date - A")
    number_of_effective_day_2 = fields.Integer('Number of effective day (B)', help="Booking date + B")
    day_effect = fields.Datetime('Day Effect', compute='_get_day_effect_and_expire', store=True)
    day_expire = fields.Datetime('Day Expire', compute='_get_day_effect_and_expire', store=True)
    # TODO hainn1 Tại sao cần lưu thông báo vào field này, có thể sử dụng compute trong trường hợp này
    booking_notification = fields.Char('Thông báo của Booking')
    statement_service_ids = fields.One2many('statement.service', 'booking_id',
                                            string='Lịch trình thanh toán')
    REASON_NOT_BK = [('expensive', 'Giá cao'), ('not_belive', 'Chưa  tin tưởng'), ('insurance', 'Bảo hiểm'),
                     ('doctor', 'Bác sĩ'), ('effective', 'Hiệu quả'), ('bad_weather', 'Thời  tiết xấu'),
                     ('far_from_home', 'Nhà xa'), ('not_find_time', 'Chưa thu xếp được thời gian'),
                     ('not_enough_finance', 'Chưa đủ tài chính'), ('other', 'Lý do khác')]
    reason_not_booking_date = fields.Selection(REASON_NOT_BK, string='Lý do chưa hẹn lịch')
    REASON_OUT_SOLD = [('think_more', 'Suy nghĩ thêm'), ('ask_relationship', 'Hỏi ý kiến người thân'),
                       ('not_enough_money', 'Chưa đủ chi phí thực hiện'), ('being_treated', 'Sức khỏe chưa đảm bảo'),
                       ('not_enough_consult', 'Bác sĩ tư vấn chưa đủ thời gian để làm DV'),
                       ('consult_not_improve', 'Bác sĩ tư vấn không cải thiện'),
                       ('treated_another_company', 'Đang điều trị tại cơ sở khác'),
                       ('1', 'Tư vấn tham khảo chưa có nhu cầu'),
                       ('2', 'KH trên 60 tuổi'),
                       ('3', 'KH chờ người nhà,tái khám,thay băng,cắt chỉ nên tư vấn tham khảo'),
                       ('4', 'KH không đủ thời gian ở Việt Nam'),
                       ('5', 'Nhu cầu khách hàng quá cao cơ sở không đáp ứng được'),
                       ('6', 'KH dưới 18 tuổi'),
                       ('7', 'Trùng Booking cũ'),
                       ('8', 'Chất lượng tư vấn (Không đồng nhất (Chuyên môn/chi phí), thái độ tư vấn...)'),
                       ('9', 'KH đến tư vấn trực tiếp nhưng vội về,báo giá qua điện thoại'),
                       ('10', 'Chỉ có nhu cầu nhận quà tặng'),
                       ('11', 'Khách cắt chỉ,tái khám,thay băng,tư vấn tham khảo thêm'),
                       ('12', 'Không cải thiện'),('13', 'Chi phí cao hơn các đơn vị khác'),
                       ('14', 'Không đủ chi phí'),
                       ('15', 'Phát sinh chi phí với dự tính ban đầu'), ('16', 'Chưa sắp xếp được thời gian'),
                       ('17', 'Chưa tin tưởng về chất lượng (Chuyên môn, cơ sở)'),
                       ('18', 'Gặp vấn đề tâm lý (Sợ đau/lo lắng...)'), ('19', 'Người thân không cho làm'),
                       ('20', 'Tham khảo thêm cơ sở khác'),
                       ('21', 'Chống chỉ định bác sĩ'), ('22', 'Khách hàng mang thai'), ('23', 'Độ tuổi không phù hợp')]
    reason_out_sold = fields.Selection(REASON_OUT_SOLD, string='Lý do out sold')
    date_out_sold = fields.Date('Ngày out sold')
    REASON_CANCEL_BOOKING = [('cus_cancel_booking_date', 'Khách hàng hủy lịch'),
                             ('cus_are_being_treated', 'Khách đang điều trị bệnh lý'),
                             ('wrong_appointment', 'Thao tác sai lịch hẹn'), ('other', 'Lý do khác (Ghi rõ nội dung)')]
    reason_cancel_booking = fields.Selection(REASON_CANCEL_BOOKING, string='Lý do hủy')

    ad_id = fields.Char('AD ID')
    gclid = fields.Char('Gclid')

    kept_coupon = fields.Many2many('crm.discount.program', string='Giữ chương trình khuyến mại')
    kept_campaign = fields.Many2many('utm.campaign', string='Giữ chiến dịch')

    # PHÂN LOẠI KHÁCH HÀNG MẮC COVID
    people_infected_with_covid = fields.Boolean(string='Khách hàng mắc covid-19', default=False, tracking=True)
    tested_positive_date = fields.Date(string='Ngày mắc covid', tracking=True)

    # PHÂN LOẠI NGÀY KHÁCH HÀNG HẸN ĐẾN
    EXPECTED_DAY = [('weekday', 'Ngày thường (Thứ 2 - Thứ 6)'),
                    ('weekend', 'Cuối tuần( Thứ 7, Chủ nhật')]
    expected_day = fields.Selection(EXPECTED_DAY, string='Phân loại ngày hẹn lịch')

    # CRM HỒNG HÀ
    aliases = fields.Char('Bí danh')
    product_category_ids = fields.Many2many('product.category', 'crm_lead_product_category_rel', 'lead_id',
                                            'product_category_id',
                                            string='Nhóm dịch vụ', domain="[('brand_id', '=', brand_id)]")
    is_hh = fields.Boolean('Brand Hồng Hà', compute='check_hh', default=False)
    ward_id = fields.Many2one('res.country.ward', string='Phường/ Xã')
    # Thêm công nợ cho khách vào booking mà không đưa vào payment
    # Khi có
    add_amount_paid_crm = fields.Monetary('Tiền khách trả', default=0, store=True)

    khach_hang_gioi_thieu = fields.Many2one('res.partner', string='Khách hàng giới thiệu',
                                            help='Đây là khách hàng đã giới thiệu khách hàng trên Booking')
    is_khach_hang_gioi_thieu = fields.Boolean(related='source_id.khach_hang_gioi_thieu')

    # @api.depends('partner_id', 'type')
    # def check_new_customer(self):
    #     for record in self:
    #         if record.partner_id:
    #             won_booking = self.env['crm.lead'].search([('type', '=', 'opportunity'), ('partner_id', '=',)])
    TYPE_PARTNER = [('old', 'Khách hàng cũ'), ('new', 'Khách hàng mới')]
    type_data_partner = fields.Selection(TYPE_PARTNER, string='Loại khách hàng')

    @api.model
    def create(self, vals_list):
        res = super(CRM, self).create(vals_list)
        partner = res.partner_id
        if ('sale' in partner.sudo().sale_order_ids.mapped('state')) or (
                'done' in partner.sudo().sale_order_ids.mapped('state')):
            res.type_data_partner = 'old'
            partner.type_data_partner = 'old'
        elif 'old' in partner.crm_ids.mapped('type_data_partner'):
            res.type_data_partner = 'old'
            partner.type_data_partner = 'old'
        else:
            res.type_data_partner = 'new'
            partner.type_data_partner = 'new'
        return res

    @api.onchange('people_infected_with_covid')
    def onchange_people_infected_with_covid(self):
        self.tested_positive_date = False
        if self.people_infected_with_covid:
            self.tested_positive_date = date.today()

    @api.depends('brand_id')
    def check_hh(self):
        for rec in self:
            rec.is_hh = True if rec.brand_id.code == "HH" else False

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|', '|', ('name', operator, name), ('phone', operator, name),
                      ('mobile', operator, name),
                      ('contact_name', operator, name), ('code_customer', operator, name)]
        partner_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(partner_id).name_get()

    @api.onchange('brand_id')
    def get_campain_id(self):
        domain = [('campaign_status', '=', '2')]
        if self.brand_id:
            domain += [('brand_id', '=', self.brand_id.id)]
        return {'domain': {'campaign_id': [('id', 'in', self.env['utm.campaign'].search(domain).ids)]}}

    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.state_id:
            return {'domain': {'district_id': [
                ('id', 'in', self.env['res.country.district'].search([('state_id', '=', self.state_id.id)]).ids)]}}

    # @api.depends('price_list_id')
    # def _get_type_booking(self):
    #     for record in self:
    #         if record.price_list_id:
    #             record.is_guarantee = True if record.price_list_id.type == 'guarantee' else False
    #         print(record.is_guarantee)
    # @api.constrains('birth_date', 'year_of_birth')
    # def constrains_year_date(self):
    #     for record in self:
    #         print(record.year_of_birth, '*'*100)
    #         try:
    #             year_of_birth = int(record.year_of_birth)
    #         except:
    #             raise ValidationError('Năm sinh không hợp lệ')
    #         if record.birth_date and record.year_of_birth and record.birth_date.year != year_of_birth:
    #             raise ValidationError("Giá trị trường năm sinh không trùng với năm của trường ngày sinh")

    @api.onchange('company_id')
    def _onchange_action(self):
        domain = {'brand_id': [('id', 'in', self.company_id.brand_ids.ids)]}
        self.brand_id = self.company_id.brand_id.id
        return {'domain': domain}

    @api.onchange('category_source_id')
    def onchange_by_category(self):
        if self.category_source_id and self.source_id.category_id != self.category_source_id:
            self.source_id = False

    @api.onchange('country_id')
    def onchange_by_country(self):
        if self.state_id and self.state_id.country_id != self.country_id:
            self.state_id = False
            self.street = False

    @api.depends('create_uid')
    def set_department(self):
        for rec in self:
            rec.department_id = False
            if rec.create_uid:
                employee_id = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', rec.create_uid.id)])
                rec.department_id = employee_id.department_id.id

    # @api.constrains('phone_relatives')
    # def check_phone_relatives(self):
    #     for rec in self:
    #         if rec.phone_relatives:
    #             if rec.phone_relatives.isdigit() is False:
    #                 raise ValidationError('Điện thoại người thân 1 chỉ nhận giá trị số')
    #             elif len(rec.phone_relatives) > 10:
    #                 raise ValidationError('Điện thoại người thân 1 không được vượt quá 10 kí tự')

    @api.constrains('year_of_birth')
    def validate_year(self):
        for rec in self:
            if rec.year_of_birth:
                try:
                    if int(rec.year_of_birth) >= date.today().year:
                        raise ValidationError('Năm sinh phải nhỏ hơn năm hiện tại')
                except:
                    raise ValidationError('Năm sinh không hợp lệ')

    @api.constrains('pass_port_date')
    def validate_passport_date(self):
        for rec in self:
            date_check_max = date.today() + timedelta(days=365*20)
            date_check_min = date.today() - timedelta(days=365*20)
            if rec.pass_port_date and (rec.pass_port_date.year > date_check_max.year):
                raise ValidationError('Ngày cấp CMT/CCCD không hợp lệ.\nCMT/CCCD đã hết hạn')
            if rec.pass_port_date and (rec.pass_port_date.year < date_check_min.year):
                raise ValidationError('Ngày cấp CMT/CCCD không hợp lệ.\nCMT/CCCD đã hết hạn')


    # @api.constrains('mobile_relatives')
    # def check_mobile_relatives(self):
    #     for rec in self:
    #         if rec.mobile_relatives:
    #             if rec.mobile_relatives.isdigit() is False:
    #                 raise ValidationError('Điện thoại người thân 2 chỉ nhận giá trị số')
    #             elif len(rec.mobile_relatives) > 10:
    #                 raise ValidationError('Điện thoại người thân 2 không được vượt quá 10 kí tự')
    #             elif rec.phone_relatives and rec.mobile_relatives == rec.phone_relatives:
    #                 raise ValidationError('Điện thoại người thân 2 không được trùng với Điện thoại người thân 1')

    @api.constrains('phone', 'country_id')
    def check_phone(self):
        for rec in self:
            if rec.phone and rec.country_id:
                if rec.phone.isdigit() is False:
                    raise ValidationError('Điện thoại 1 khách hàng chỉ nhận giá trị số')
                # if (10 > len(rec.phone)) or (len(rec.phone) > 10) and (rec.country_id == self.env.ref('base.vn')):
                if (10 > len(rec.phone)) or (len(rec.phone) > 10):
                    if rec.country_id == self.env.ref('base.vn'):
                        raise ValidationError('Số điện thoại ở Việt Nam chỉ chấp nhận 10 kí tự')

    @api.constrains('mobile')
    def mobile_constrains(self):
        if self.mobile:
            if self.mobile.isdigit() is False:
                raise ValidationError('Trường ĐIỆN THOẠI 2 chỉ nhận giá trị số')
            # elif (10 > len(self.phone)) or (len(self.phone) > 11):
            #     raise ValidationError('Điện thoại 2 không hợp lệ')

    # @api.onchange('country_id')
    # def check_phone(self):
    #     if self.country_id and self.phone:
    #         if (10 > len(self.phone)) or (len(self.phone) > 11) and (self.country_id == self.env.ref('base.vn')):
    #             print('hello')
    #             print(self.country_id == self.env.ref('base.vn'))
    #             print(self.country_id.name)
    #             raise ValidationError('Điện thoại 1 không hợp lệ')

    @api.constrains('mobile')
    def check_mobile(self):
        for rec in self:
            if rec.mobile:
                if rec.mobile.isdigit() is False:
                    raise ValidationError('Điện thoại 2 chỉ nhận giá trị số')
                # elif len(rec.mobile) > 10:
                #     raise ValidationError('Điện thoại 2 không được vượt quá 10 kí tự')
                elif rec.phone and rec.mobile == rec.phone:
                    raise ValidationError('Điện thoại 2 không được trùng với điện thoại 1')

    def update_source(self):
        self.ensure_one()
        if self.crm_line_ids:
            return {
                'name': 'Cập nhập nguồn',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('crm_base.wizard_update_source').id,
                'res_model': 'crm.line.update.source',
                'context': {
                    'default_booking_id': self.id,
                },
                'target': 'new',
            }

    def open_case(self):
        self.ensure_one()
        return {
            'name': 'TẠO KHIẾU NẠI',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.crm_case_view_form').id,
            'res_model': 'crm.case',
            'context': {
                'default_brand_id': self.brand_id.id,
                'default_company_id': self.company_id.id,
                'default_booking_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_phone': self.partner_id.phone,
                'default_country_id': self.country_id.id,
                'default_state_id': self.state_id.id,
                'default_street': self.street,
                'default_account_facebook': self.facebook_acc,
            },
        }

    def create_phone_call_info(self):
        pc = self.env['crm.phone.call'].create({
            'name': 'Hỏi thêm thông tin - %s' % self.name,
            'subject': 'Hỏi thêm thông tin',
            'partner_id': self.partner_id.id,
            'phone': self.partner_id.phone,
            'direction': 'in',
            'company_id': self.company_id.id,
            'crm_id': self.id,
            'country_id': self.country_id.id,
            'street': self.street,
            'type_crm_id': self.env.ref('crm_base.type_phone_call_customer_ask_info').id,
            # 'booking_date': self.booking_date,
            'call_date': datetime.now(),
        })

        return {
            'name': 'Phone call',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': pc.id,
            'view_id': self.env.ref('crm_base.view_form_phone_call').id,
            'res_model': 'crm.phone.call',
            'context': {},
        }

    @api.depends('booking_ids')
    def set_check_booking(self):
        for rec in self:
            rec.check_booking = False
            if rec.booking_ids:
                rec.check_booking = True
            else:
                rec.check_booking = False

    # @api.depends('stage_id')
    # def set_check_won(self):
    #     for rec in self:
    #         rec.check_won = False
    #         if rec.stage_id == self.env.ref('crm.stage_lead4'):
    #             rec.check_won = True

    def reopen_lead(self):
        self.stage_id = self.env.ref('crm_base.crm_stage_re_open').id
        self.re_open = True

    @api.model
    def action_reopen_lead(self):
        active_ids = self.env.context.get('active_ids')
        lead = self.env['crm.lead'].browse(active_ids)
        if lead.type == 'opportunity':
            raise ValidationError('Đây là Booking. Bạn chỉ có thể mở lại Lead')
        else:
            lead.reopen_lead()

    @api.onchange('customer_come')
    def set_stage_customer_come(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id), ('active', '=', True)], limit=1)

        # Nếu tài khoản gán với nhân viên phòng Sale
        if employee and employee.department_id and (('Sale' in employee.department_id.name) or ('Marketing' in employee.department_id.name)):
            raise ValidationError(
                'Phòng ban Sale & Marketing không được thao tác chuyển trạng thái khách hàng đến cửa.')
        # Nếu tài khoản không được gán với nhân viên
        # elif employee and (self.env.user.id not in [1, 2]):
        #     raise ValidationError('Tài khoản của bạn chưa được gán với nhân viên nào.')
        else:
            if self.customer_come == 'yes':
                if self.stage_id in [self.env.ref('crm_base.crm_stage_not_confirm'),
                                     self.env.ref('crm_base.crm_stage_no_come')]:
                    self.stage_id = self.env.ref('crm_base.crm_stage_confirm').id
                self.arrival_date = fields.Datetime.now()
            else:
                self.arrival_date = False

    def update_info(self):
        self.ensure_one()
        self.stage_id = self.env.ref('crm_base.crm_stage_booking').id
        self.re_open = False
        if self.booking_ids:
            for rec in self.booking_ids:
                rec.write({
                    'contact_name': self.contact_name,
                    # 'phone': self.phone,
                    'customer_classification': self.customer_classification,
                    'aliases': self.aliases,
                    'mobile': self.mobile,
                    'gender': self.gender,
                    'country_id': self.country_id.id,
                    'state_id': self.state_id.id,
                    'district_id': self.district_id.id,
                    'street': self.street,
                    'birth_date': self.birth_date,
                    'year_of_birth': self.year_of_birth,
                    'career': self.career,
                    'pass_port': self.pass_port,
                    'pass_port_date': self.pass_port_date,
                    'pass_port_issue_by': self.pass_port_issue_by,
                    'pass_port_address': self.pass_port_address,
                    'facebook_acc': self.facebook_acc,
                    'zalo_acc': self.zalo_acc,
                    'send_info_facebook': self.send_info_facebook,
                    'send_info_zalo': self.send_info_zalo,
                    'overseas_vietnamese': self.overseas_vietnamese,
                    'email_from': self.email_from,
                    'work_online': self.work_online,
                    'shuttle_bus': self.shuttle_bus,
                    'online_counseling': self.online_counseling,
                })
                if self.fam_ids:
                    for fam in self.fam_ids:
                        fam_id = self.env['crm.family.info'].create({
                            'crm_id': rec.id,
                            'member_name': fam.member_name,
                            'type_relation_id': fam.type_relation_id.id,
                            'phone': fam.phone,
                            'address': fam.address
                        })
                        fam.sudo().unlink()

        if self.partner_id:
            self.partner_id.write({
                'name': self.contact_name,
                'aliases': self.aliases,
                # 'phone': self.phone,
                'mobile': self.mobile,
                'gender': self.gender,
                'year_of_birth': self.year_of_birth,
                'pass_port': self.pass_port,
                'career': self.career,
                'pass_port_date': self.pass_port_date,
                'pass_port_issue_by': self.pass_port_issue_by,
                'pass_port_address': self.pass_port_address,
                'country_id': self.country_id.id,
                'state_id': self.state_id.id,
                'district_id': self.district_id.id,
                'street': self.street,
                'acc_facebook': self.facebook_acc,
                'acc_zalo': self.zalo_acc,
            })

    @api.onchange('phone')
    def check_partner_lead(self):
        if self.phone:
            if self.phone.isdigit() is False:
                raise ValidationError('Điện thoại 1 khách hàng chỉ nhận giá trị số')
            # if self.env.user_id != self.create_uid or not self.env.user.has_group('base.group_system'):
            #     raise ValidationError('Bạn không có quyền chỉnh sửa số điện thoại khách hàng tại Lead/Booking này')
            if not self.env.context.get('default_phone') and self.type == 'lead' and self.stage_id != self.env.ref(
                    'crm_base.crm_stage_re_open'):
                partner = self.env['res.partner'].search([('phone', '=', self.phone)])

                lead_ids = self.env['crm.lead'].search(
                    [('phone', '=', self.phone), ('brand_id', '=', self.brand_id.id)], order="id asc", limit=1)
                if partner:
                    self.partner_id = partner.id
                    self.customer_classification = partner.customer_classification
                    self.aliases = partner.aliases
                    self.gender = partner.gender
                    self.birth_date = partner.birth_date
                    self.overseas_vietnamese = partner.overseas_vietnamese
                    self.country_id = partner.country_id.id
                    self.state_id = partner.state_id.id
                    self.district_id = partner.district_id.id
                    self.ward_id = partner.ward_id.id
                    self.street = partner.street
                    self.career = partner.career
                    self.mobile = partner.mobile
                    self.year_of_birth = partner.year_of_birth
                    self.pass_port = partner.pass_port
                    self.pass_port_date = partner.pass_port_date
                    self.pass_port_issue_by = partner.pass_port_issue_by
                    self.pass_port_address = partner.pass_port_address
                    self.contact_name = partner.name
                    self.type_data = 'old'
                else:
                    self.partner_id = False
                    self.gender = lead_ids.gender
                    self.birth_date = lead_ids.birth_date
                    self.country_id = lead_ids.country_id.id if lead_ids else self.country_id
                    self.state_id = lead_ids.state_id.id
                    self.street = lead_ids.street
                    self.customer_classification = lead_ids.customer_classification if lead_ids else "1"
                    self.mobile = lead_ids.mobile
                    self.year_of_birth = lead_ids.year_of_birth
                    self.career = lead_ids.career
                    self.pass_port = lead_ids.pass_port
                    self.contact_name = lead_ids.contact_name
                    self.aliases = lead_ids.aliases
                    self.source_id = lead_ids.source_id.id
                    self.type_data = 'new'
                    self.category_source_id = lead_ids.source_id.category_id.id
                    self.email_from = lead_ids.email_from
                    self.facebook_acc = lead_ids.facebook_acc

    @api.onchange('partner_id', 'type_data', 'source_id')
    def onchange_source_id(self):
        if self.type_data == 'new' and not self.partner_id:
            self.original_source_id = self.source_id.id
        elif self.type_data == 'old' and self.partner_id:
            self.original_source_id = self.partner_id.source_id.id if self.partner_id.source_id else False

    def open_discount_review(self):
        # if not self.crm_line_ids:
        #     raise ValidationError(_('Booking does not contain services'))
        if self.stage_id in [self.env.ref('crm_base.crm_stage_not_confirm'),
                             self.env.ref('crm_base.crm_stage_out_sold'), self.env.ref('crm_base.crm_stage_cancel')]:
            raise ValidationError(
                _('Bạn không thể áp dụng GIẢM GIÁ SÂU cho trường hợp KHÁCH CHƯA ĐẾN, BOOKING HỦY/OUT SOLD'))
        else:
            return {
                'name': 'GIẢM GIÁ SÂU',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('crm_base.view_discount_review').id,
                'res_model': 'discount.review',
                'context': {
                    'default_booking_id': self.id,
                    'default_type': 'booking',
                    'default_partner_id': self.partner_id.id,
                    'default_crm_line_ids': self.crm_line_ids.ids,
                },
                'target': 'new',
            }

    @api.onchange('contact_name')
    def set_upper_name(self):
        if self.contact_name:
            contact = self.contact_name
            self.contact_name = contact.upper()

    @api.onchange('contact_name')
    def set_name_lead(self):
        if self.type == 'lead':
            self.name = self.contact_name
            if self.contact_name:
                self.name = self.contact_name.upper()

    def clone_lead(self):
        return {
            'name': 'LEAD',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.form_crm_lead').id,
            'res_model': 'crm.lead',
            'context': {
                'default_phone': self.phone,
                'default_name': self.name,
                'default_contact_name': self.contact_name,
                'default_code_customer': self.code_customer,
                'default_customer_classification': self.customer_classification,
                'default_partner_id': self.partner_id.id,
                'default_aliases': self.aliases,
                'default_type_crm_id': self.type_crm_id.id,
                'default_type': self.type,
                'default_type_data': 'old',
                'default_gender': self.gender,
                'default_birth_date': self.birth_date,
                'default_year_of_birth': self.year_of_birth,
                'default_mobile': self.mobile,
                'default_career': self.career,
                'default_pass_port': self.pass_port,
                'default_pass_port_date': self.pass_port_date,
                'default_pass_port_issue_by': self.pass_port_issue_by,
                'default_pass_port_address': self.pass_port_address,
                'default_country_id': self.country_id.id,
                'default_state_id': self.state_id.id,
                'default_district_id': self.district_id.id,
                'default_street': self.street,
                'default_email_from': self.email_from,
                'default_facebook_acc': self.facebook_acc,
                'default_zalo_acc': self.zalo_acc,
                'default_stage_id': self.env.ref('crm_base.crm_stage_no_process').id,
                'default_company_id': self.company_id.id,
                'default_description': 'COPY',
                'default_special_note': self.special_note,
                'default_price_list_id': self.price_list_id.id if self.price_list_id.active else False,
                'default_currency_id': self.currency_id.id,
                # 'default_source_id': self.source_id.id,
                # 'default_campaign_id': self.campaign_id.id,
                # 'default_medium_id': self.medium_id.id,
                # 'default_category_source_id': self.category_source_id.id,
                'default_work_online': self.work_online,
                'default_send_info_facebook': self.send_info_facebook,
                'default_online_counseling': self.online_counseling,
                'default_shuttle_bus': self.shuttle_bus,
                'default_is_clone': True
            },
        }

    def share_booking(self):
        return {
            'name': 'Chi nhánh được chia sẻ',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_share_booking').id,
            'res_model': 'share.booking',
            'context': {
                'default_booking_id': self.id,
            },
            'target': 'new',
        }

    def cancel_booking(self):
        return {
            'name': 'Đóng Booking',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_form_cancel_booking').id,
            'res_model': 'cancel.booking',
            'context': {
                'default_booking_id': self.id,
            },
            'target': 'new',
        }

    def create_booking_guarantee(self):
        return {
            'name': 'Tạo Booking bảo hành',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_form_create_booking_guarantee').id,
            'res_model': 'crm.create.guarantee',
            'context': {
                'default_crm_id': self.id,
                'default_brand_id': self.brand_id.id,
                'default_partner_id': self.partner_id.id,
            },
            'target': 'new',
        }

    def qualify_partner(self):
        return {
            'name': 'THÔNG TIN LỊCH HẸN',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.check_partner_view_form').id,
            'res_model': 'check.partner.qualify',
            'context': {
                'default_name': self.contact_name,
                'default_phone': self.phone,
                'default_lead_id': self.id,
                'default_company_id': self.company_id.id,
                'default_type': self.type,
                'default_partner_id': self.partner_id.id,
            },
            'target': 'new',
        }

    def action_add_amount_paid_crm(self):
        return {
            'name': 'Chỉnh tiền khách trả',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_add_amount_paid_crm').id,
            'res_model': 'crm.lead.paid',
            'context': {
                'default_crm_id': self.id,
            },
            'target': 'new',
        }

    def apply_prg(self):
        return {
            'name': 'Áp dụng coupon',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_apply_discount_prg').id,
            'res_model': 'crm.apply.discount.program',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_crm_id': self.id,
            },
            'target': 'new',
        }

    @api.onchange('company_id')
    def reset_sale_team(self):
        if 'default_price_list_id' in self._context:
            self.price_list_id = self._context.get('default_price_list_id')
        else:
            self.price_list_id = False
        self.team_id = False

    @api.onchange('birth_date')
    def set_year_of_birth(self):
        if self.birth_date:
            self.year_of_birth = self.birth_date.year

    @api.onchange('company_id')
    def set_price_list(self):
        if 'default_price_list_id' in self._context:
            self.price_list_id = self._context.get('default_price_list_id')
        elif self.company_id:
            self.price_list_id = False

    @api.constrains('booking_date')
    def constrain_booking_date(self):
        for record in self:
            now = datetime.now()
            if record.booking_date and record.type == 'opportunity':
                limited_time = record.create_date + timedelta(days=720)
                if record.booking_date and record.booking_date >= limited_time:
                    raise ValidationError('Giá trị ngày hẹn lịch không hợp lệ')
                if record.booking_date.date() < now.date():
                    raise ValidationError('Ngày hẹn lịch không được nhỏ hơn ngày hiện tại !!!')

    # @api.constrains('number_of_booking_date_changes')
    # def constrain_booking_date(self):
    #     for record in self:
    #         if record.number_of_booking_date_changes:
    #             if record.number_of_booking_date_changes > 2:
    #                 raise ValidationError('Ngày hẹn lịch không được thay đổi quá 2 lần !!!')

    @api.depends('booking_date', 'number_of_effective_day_1', 'number_of_effective_day_2', 'stage_id')
    def _get_day_effect_and_expire(self):
        for record in self:
            if record.booking_date and record.stage_id != self.env.ref('crm_base.crm_stage_paid'):
                record.day_effect = record.booking_date - timedelta(
                    days=record.number_of_effective_day_1) if record.number_of_effective_day_1 else False
                record.day_expire = record.booking_date + timedelta(
                    days=record.number_of_effective_day_2) if record.number_of_effective_day_2 else False

    def set_effect(self, day_effect, day_expire):
        now = datetime.now()
        if day_expire:
            if day_effect and day_expire and (now.date() >= day_effect.date()) and (now.date() <= day_expire.date()):
                effect = 'effect'
            elif day_expire and now.date() <= day_expire.date():
                effect = 'effect'
            elif day_expire and now.date() > day_expire.date():
                effect = 'expire'
            else:
                effect = 'not_valid'
            return effect

    def update_partner(self, vals):  # Hàm Cập nhật thông tin khách hàng
        if self.partner_id:
            partner = self.partner_id
            crm_ids = partner.crm_ids
            if ('aliases' in vals) and vals['aliases'] and partner.aliases != vals['aliases']:
                partner.aliases = vals['aliases']
                if crm_ids:
                    for record in crm_ids:
                        record.aliases = vals['aliases'] if record.aliases != vals['aliases'] else record.aliases
            if ('mobile' in vals) and vals['mobile'] and partner.mobile != vals['mobile']:
                partner.mobile = vals['mobile']
                # if crm_ids:
                #     for record in crm_ids:
                #         record.mobile = vals['mobile'] if record.mobile != vals['mobile'] else record.mobile
                # if self.lead_id and (self in self.lead_id.booking_ids):
                if self.lead_id and (self.lead_id.type == 'lead'):
                    self.lead_id.mobile = vals['mobile'] if self.lead_id.mobile != vals['mobile'] else self.lead_id.mobile
            if ('contact_name' in vals) and vals['contact_name'] and partner.name != vals['contact_name']:
                partner.name = vals['contact_name']
                if crm_ids:
                    if self.lead_id and self.lead_id.type == 'lead':
                        self.lead_id.name = vals['contact_name']
                        self.lead_id.contact_name = vals['contact_name'] if self.lead_id.contact_name != vals['contact_name'] else self.lead_id.contact_name
                    # for record in crm_ids:
                    #     record.contact_name = vals['contact_name'] if record.contact_name != vals['contact_name'] else record.contact_name
                        # record.name = vals['contact_name'] if ((record.name != vals['contact_name']) and (record.type == 'lead')) else record.name
            if ('overseas_vietnamese' in vals) and vals['overseas_vietnamese'] and partner.overseas_vietnamese != vals['overseas_vietnamese']:
                partner.overseas_vietnamese = vals['overseas_vietnamese']
                if crm_ids:
                    for record in crm_ids:
                        record.overseas_vietnamese = vals['overseas_vietnamese'] if record.overseas_vietnamese != vals['overseas_vietnamese'] else record.overseas_vietnamese
            if ('birth_date' in vals) and vals['birth_date'] and partner.birth_date != vals['birth_date']:
                partner.birth_date = vals['birth_date']
                partner.year_of_birth = partner.birth_date.year
                if crm_ids:
                    for record in crm_ids:
                        record.birth_date = vals['birth_date'] if record.birth_date != vals['birth_date'] else record.birth_date
                        record.year_of_birth = record.birth_date.year
            if ('email_from' in vals) and vals['email_from'] and partner.email != vals['email_from']:
                partner.email = vals['email_from']
                if crm_ids:
                    for record in crm_ids:
                        record.email_from = vals['email_from'] if record.email_from != vals['email_from'] else record.email_from
            if ('career' in vals) and vals['career'] and partner.career != vals['career']:
                partner.career = vals['career']
                if crm_ids:
                    for record in crm_ids:
                        record.career = vals['career'] if record.career != vals['career'] else record.career
            if ('pass_port' in vals) and vals['pass_port'] and partner.pass_port != vals['pass_port']:
                partner.pass_port = vals['pass_port']
                if crm_ids:
                    for record in crm_ids:
                        record.pass_port = vals['pass_port'] if record.pass_port != vals['pass_port'] else record.pass_port
            if ('pass_port_date' in vals) and vals['pass_port_date'] and partner.pass_port_date != vals['pass_port_date']:
                partner.pass_port_date = vals['pass_port_date']
                if crm_ids:
                    for record in crm_ids:
                        record.pass_port_date = vals['pass_port_date'] if record.pass_port_date != vals['pass_port_date'] else record.pass_port_date
            if ('pass_port_issue_by' in vals) and vals['pass_port_issue_by'] and partner.pass_port_issue_by != vals['pass_port_issue_by']:
                partner.pass_port_issue_by = vals['pass_port_issue_by']
                if crm_ids:
                    for record in crm_ids:
                        record.pass_port_issue_by = vals['pass_port_issue_by'] if record.pass_port_issue_by != vals['pass_port_issue_by'] else record.pass_port_issue_by
            if ('pass_port_address' in vals) and vals['pass_port_address'] and partner.pass_port_address != vals['pass_port_address']:
                partner.pass_port_address = vals['pass_port_address']
                if crm_ids:
                    for record in crm_ids:
                        record.pass_port_address = vals['pass_port_address'] if record.pass_port_address != vals['pass_port_address'] else record.pass_port_address
            if ('street' in vals) and vals['street'] and partner.street != vals['street']:
                partner.street = vals['street']
                if crm_ids:
                    for record in crm_ids:
                        record.street = vals['street'] if record.street != vals['street'] else record.street
            if ('district_id' in vals) and vals['district_id'] and partner.district_id.id != vals['district_id']:
                partner.district_id = vals['district_id']
                if crm_ids:
                    for record in crm_ids:
                        record.district_id = vals['district_id'] if record.district_id.id != vals['district_id'] else record.district_id.id

            if ('ward_id' in vals) and vals['ward_id'] and partner.ward_id.id != vals['ward_id']:
                partner.ward_id = vals['ward_id']
                if crm_ids:
                    for record in crm_ids:
                        record.ward_id = vals['ward_id'] if record.ward_id.id != vals['ward_id'] else record.ward_id.id

            if ('state_id' in vals) and vals['state_id'] and partner.state_id.id != vals['state_id']:
                partner.state_id = vals['state_id']
                if crm_ids:
                    for record in crm_ids:
                        record.state_id = vals['state_id'] if record.state_id.id != vals['state_id'] else record.state_id.id

            if ('country_id' in vals) and vals['country_id'] and partner.country_id.id != vals['country_id']:
                partner.country_id = vals['country_id']
                if crm_ids:
                    for record in crm_ids:
                        record.country_id = vals['country_id'] if record.country_id.id != vals['country_id'] else record.country_id.id

    def write(self, vals):
        res = super(CRM, self).write(vals)
        if vals.get('booking_date') and self.id:
            pc = self.env['crm.phone.call'].search([('crm_id', '=', self.id), ('state', '=', 'draft'),
                                                    ('type_crm_id.name', 'ilike', 'Xác nhận lịch hẹn')])
            if not pc:
                CRM.create_phone_call(self, self.create_uid)
            else:
                for item in pc:
                    item.booking_date = vals.get('booking_date')
                sms = self.env['crm.sms'].search(['&', '&', ('crm_id', '=', self.id), ('state', '=', 'draft'), '|',
                                                  ('name', 'ilike', 'Xác nhận lịch hẹn'), '|',
                                                  ('name', 'ilike', 'Nhắc hẹn khách hàng lần 2'),
                                                  ('name', 'ilike', 'Nhắc hẹn khách hàng lần 1')])
                for item in sms:
                    script_sms = sms.crm_id.company_id.script_sms_id
                    booking_date = vals.get('booking_date')
                    booking_date = datetime.strptime(booking_date, '%Y-%m-%d %H:%M:%S')
                    if 'Xác nhận lịch hẹn' in item.name:
                        for rec in script_sms:
                            if rec.type == 'XNLH':
                                name = 'Xác nhận lịch hẹn - %s' % sms.crm_id.name
                                if name:
                                    content_sms = rec.content.replace('[Ten_KH]', sms.crm_id.contact_name)
                                    content_sms = content_sms.replace('[Ma_Booking]', sms.crm_id.name)
                                    content_sms = content_sms.replace('[Booking_Date]',
                                                                      sms.crm_id.booking_date.strftime('%d-%m-%Y'))
                                    content_sms = content_sms.replace('[Location_Shop]',
                                                                      sms.crm_id.company_id.location_shop)
                                    content_sms = content_sms.replace('[Ban_Do]', sms.crm_id.company_id.map_shop)
                                    if sms.crm_id.company_id.health_declaration:
                                        content_sms = content_sms.replace('[Khai_Bao]',
                                                                          sms.crm_id.company_id.health_declaration)
                                    item.write({
                                        'desc': content_sms,
                                        'send_date': datetime.now()
                                    })
                                    # item.content = content_sms
                                    # item.send_date = datetime.now()
                    if 'Nhắc hẹn khách hàng lần 2' in item.name:
                        for rec in script_sms:
                            if rec.type == 'NHKHL2':
                                name = 'Nhắc hẹn khách hàng lần 1 - %s' % sms.crm_id.name
                                if name:
                                    content_sms = rec.content.replace('[Ten_KH]', sms.crm_id.contact_name)
                                    content_sms = content_sms.replace('[Ma_Booking]', sms.crm_id.name)
                                    content_sms = content_sms.replace('[Booking_Date]',
                                                                      sms.crm_id.booking_date.strftime('%d-%m-%Y'))
                                    content_sms = content_sms.replace('[Location_Shop]',
                                                                      sms.crm_id.company_id.location_shop)
                                    content_sms = content_sms.replace('[Ban_Do]', sms.crm_id.company_id.map_shop)
                                    # item.content = content_sms
                                    # item.send_date = booking_date.replace(hour=2, minute=0, second=0)
                                    item.write({
                                        'desc': content_sms,
                                        'send_date': booking_date.replace(hour=2, minute=0, second=0)
                                    })
                    if 'Nhắc hẹn khách hàng lần 1' in item.name:
                        for rec in script_sms:
                            if rec.type == 'NHKHL1':
                                name = 'Nhắc hẹn khách hàng lần 1 - %s' % sms.crm_id.name
                                if name:
                                    content_sms = rec.content.replace('[Ten_KH]', sms.crm_id.contact_name)
                                    content_sms = content_sms.replace('[Ma_Booking]', sms.crm_id.name)
                                    content_sms = content_sms.replace('[Booking_Date]',
                                                                      sms.crm_id.booking_date.strftime('%d-%m-%Y'))
                                    content_sms = content_sms.replace('[Location_Shop]',
                                                                      sms.crm_id.company_id.location_shop)
                                    content_sms = content_sms.replace('[Ban_Do]', sms.crm_id.company_id.map_shop)
                                    # item.content = content_sms
                                    # item.send_date = booking_date.replace(hour=2, minute=0, second=0) - relativedelta(days=1)
                                    item.write({
                                        'desc': content_sms,
                                        'send_date': booking_date.replace(hour=2, minute=0, second=0) - relativedelta(
                                            days=1)
                                    })

        for rec in self:
            if vals.get('booking_date'):
                rec.number_of_booking_date_changes += 1
                rec.effect = self.set_effect(rec.day_effect, rec.day_expire)
                if rec.booking_date < datetime.now() and rec.stage_id == self.env.ref(
                        'crm_base.crm_stage_not_confirm'):
                    rec.stage_id = self.env.ref('crm_base.crm_stage_no_come').id
                elif rec.booking_date >= datetime.now() and rec.customer_come == 'no' and rec.stage_id != self.env.ref('crm_base.crm_stage_paid'):
                    rec.stage_id = self.env.ref('crm_base.crm_stage_not_confirm').id
                if rec.crm_line_ids:
                    for line in rec.crm_line_ids:
                        line.line_booking_date = vals.get('booking_date')
            rec.update_partner(vals)

        return res

    def update_booking_date(self):
        return {
            'name': 'Thay đổi ngày hẹn lịch',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.wizard_change_booking_date').id,
            'res_model': 'change.booking.date',
            'context': {
                'default_booking_id': self.id,
            },
            'target': 'new',
        }

    @api.model
    def create(self, vals):
        res = super(CRM, self).create(vals)
        if res.type == 'opportunity':
            res.stage_id = self.env.ref('crm_base.crm_stage_not_confirm').id
            # res.name = self.env['ir.sequence'].next_by_code('crm.lead')
            res.number_of_effective_day_1 = res.type_crm_id.number_of_effective_day_1 or False
            res.number_of_effective_day_2 = res.type_crm_id.number_of_effective_day_2 or False
            if res.partner_id:
                res.partner_id.write({
                    'name': res.contact_name,
                    'gender': res.gender,
                    'birth_date': res.birth_date,
                    'year_of_birth': res.year_of_birth,
                    'country_id': res.country_id.id,
                    'state_id': res.state_id.id,
                    'street': res.street,
                })
            if res.type_crm_id != self.env.ref('crm_base.type_oppor_guarantee') and not self.env.user.has_group(
                    'base.group_system'):
                booking_effect = self.env['crm.lead'].sudo().search(
                    [('type', '=', 'opportunity'), ('partner_id', '=', res.partner_id.id),
                     ('brand_id', '=', res.brand_id.id), ('effect', '=', 'effect'), ('name', '!=', res.name)])
                if booking_effect:
                    booking_names = []
                    booking_company = []
                    booking_company_names = []
                    for booking in booking_effect:
                        booking_names.append(booking.name)
                        if booking.company_id not in booking_company:
                            booking_company.append(booking.company_id)
                            booking_company_names.append(booking.company_id.name)
                    raise ValidationError('Bạn không thể tạo Booking. Mời vào %s của chi nhánh %s để thao tác.' % (
                        ', '.join(booking_names), ','.join(booking_company_names)))

            res.name = self.create_booking_code(res.type_crm_id)
            res.effect = self.set_effect(res.day_effect, res.day_expire)
        return res

    def create_booking_code(self, type_crm):
        """Hàm sinh mã Booking"""
        if type_crm == self.env.ref('crm_base.type_oppor_new'):
            sequence_code = 'crm.lead'
        else:
            sequence_code = 'crm.lead.guarantee'
        while True:
            # Tạo mã mới
            booking_code = self.env['ir.sequence'].next_by_code(sequence_code)
            # Kiểm tra xem mã đã tồn tại chưa
            existing_booking = self.env['crm.lead'].search([('name', '=', booking_code), ('type', '=', 'opportunity')])
            if not existing_booking:
                return booking_code

    def cron_update_stage_booking(self):
        # Lấy múi giờ hệ thống
        current_timezone = pytz.timezone(self.env.context.get('tz') or 'UTC')
        # Lấy ngày và giờ hiện tại theo múi giờ hệ thống
        current_datetime = datetime.now(current_timezone)
        # CẬP NHẬT HIỆU LỰC BOOKING
        # booking_effect = self.env['crm.lead'].search(
        #     [('type', '=', 'opportunity'), ('effect', '=', 'effect'), ('day_expire', '<', current_datetime.date())])
        # if booking_effect:
        #     for booking in booking_effect:
        #         booking.effect = 'expire'
        #         booking.booking_notification = "Booking hết hiệu lực. Bạn chỉ có thể tạo được phiếu khám từ Booking này."
        query_1 = """
            UPDATE crm_lead 
            SET effect = 'expire', booking_notification = 'Booking hết hiệu lực. Bạn chỉ có thể tạo được phiếu khám từ Booking này.'
            WHERE type = 'opportunity' AND effect = 'effect' AND day_expire < '%s'
        """ % current_datetime.date()
        self.env.cr.execute(query_1)
        # CẬP NHẬT TRẠNG THÁI KHÁCH KHÔNG ĐẾN CHO BOOKING ĐỐI VỚI BOOKING ĐANG Ở TRẠNG THÁI CHƯA XÁC NHẬN
        # booking_not_confirm = self.env['crm.lead'].search(
        #     [('type', '=', 'opportunity'), ('stage_id', '=', self.env.ref('crm_base.crm_stage_not_confirm').id),
        #      ('booking_date', '<', current_datetime)])
        # if booking_not_confirm:
        #     for booking in booking_not_confirm:
        #         booking.stage_id = self.env.ref('crm_base.crm_stage_no_come').id

        not_confirm = self.env.ref('crm_base.crm_stage_not_confirm')
        no_come = self.env.ref('crm_base.crm_stage_no_come')
        query_2 = """
            UPDATE crm_lead 
            SET stage_id = %s
            WHERE type = 'opportunity' AND stage_id = %s AND booking_date < '%s'
        """ % (no_come.id, not_confirm.id, current_datetime)
        self.env.cr.execute(query_2)
        # if self.env['ir.config_parameter'].sudo().get_param('web.base.url') == 'https://erp.scigroup.com.vn':
        #     body = 'Đã chạy cron Update Booking'
        #     url = "https://api.telegram.org/bot6480280702:AAEQfjmvu6OudkToWg2jxtEmigGSY7J3ljA/sendMessage?chat_id=-4035923819&text=%s" % body
        #     payload = {}
        #     headers = {}
        #     requests.request("GET", url, headers=headers, data=payload)

    def select_service(self):
        return {
            'name': 'Lựa chọn dịch vụ',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_form_crm_select_service').id,
            'res_model': 'crm.select.service',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_booking_id': self.id,
            },
            'target': 'new',
        }

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(CRM, self).fields_get(allfields, attributes=attributes)

        # Xử lý không cho xuất số điện thoại
        for field_name in fields:
            if field_name in ['phone', 'mobile', 'partner_address_phone']:
                fields[field_name]['exportable'] = False

        return fields

    @api.depends('add_amount_paid_crm', 'payment_ids.state', 'payment_ids.payment_type', 'payment_ids.amount')
    def set_paid_booking(self):
        for rec in self:
            if rec.add_amount_paid_crm > 0:
                paid = rec.add_amount_paid_crm
            else:
                paid = 0

            if rec.payment_ids:
                for pm in rec.payment_ids:
                    if pm.state in ['posted', 'reconciled']:
                        if pm.payment_type == 'inbound':
                            paid += pm.amount_vnd
                        elif pm.payment_type == 'outbound':
                            paid -= pm.amount_vnd
            rec.amount_paid = paid

    # @api.depends('order_ids.amount_total', 'order_ids.state')
    # def set_used_booking(self):
    #     for rec in self:
    #         used = 0
    #         if rec.order_ids:
    #             for record in rec.order_ids:
    #                 if record.state in ['sale', 'done']:
    #                     used += record.amount_total
    #         rec.amount_used = used

    @api.depends('order_ids.amount_total', 'order_ids.state', 'order_ids.order_line.qty_delivered')
    def set_used_booking(self):
        """
        Hàm tính tổng tiền đã sử dụng của BK: Bằng tổng của :
            + SO bán dịch vụ đã xác nhận
            + Tất cả các line có số lượng đã giao khác 0 của SO bán sản phẩm => Làm tròn
        """
        for rec in self:
            used = 0
            if rec.order_ids:
                for order in rec.order_ids:
                    if order.state in ['sale', 'done'] and order.pricelist_type != 'product':
                        used += order.amount_total
                    elif order.state in ['sale', 'done'] and order.pricelist_type == 'product':
                        line_return_amount_total = sum(
                            [line.qty_delivered * (line.price_subtotal / line.product_uom_qty) for line in
                             order.order_line])
                        used += round(line_return_amount_total / 1000) * 1000
            rec.amount_used = used

    @api.depends('crm_line_ids.total', 'crm_line_ids.stage')
    def set_total(self):
        for rec in self:
            rec.amount_total = 0
            if rec.crm_line_ids:
                for i in rec.crm_line_ids:
                    if i.stage != 'cancel':
                        rec.amount_total += i.total
                    elif i.stage == 'cancel':
                        rec.amount_total += i.unit_price * i.uom_price * i.number_used

    @api.depends('amount_paid', 'amount_used')
    def set_amount_remain(self):
        for rec in self:
            # Tổng tiền còn lại = tổng tiền đã trả - tổng tiền sử dụng
            rec.amount_remain = rec.amount_paid - rec.amount_used

    @api.depends('amount_paid', 'amount_total')
    def set_total_amount_due(self):
        for rec in self:
            rec.total_amount_due = rec.amount_total - rec.amount_paid

    def action_view_payment_booking(self):
        action = self.env.ref('account.action_account_payments').read()[0]
        action['context'] = {
            'default_partner_id': self.partner_id.id,
            'default_crm_id': self.id,
        }
        action['domain'] = [('crm_id', '=', self.id), ('state', 'in', ('draft', 'posted', 'reconciled'))]
        return action

    def action_view_sale_order(self):
        action = self.env.ref('sale.action_orders').read()[0]
        action['context'] = {
            'default_partner_id': self.partner_id.id,
            'default_booking_id': self.id,
        }
        action['domain'] = [('booking_id', '=', self.id), ('state', 'not in', ('draft', 'sent', 'cancel'))]
        return action

    def create_phone_call(self, user=None):
        if not user:
            user = self.env.user
        time = datetime.now()
        tz_current = pytz.timezone(self._context.get('tz') or 'UTC')  # get timezone user
        tz_database = pytz.timezone('UTC')
        time = tz_database.localize(time)
        time = time.astimezone(tz_current)
        time = time.date()
        days = (self.booking_date.date() - time).days
        if days > 1:
            phone_call = self.env['crm.phone.call'].with_user(user.id).sudo().create({
                'name': ('Xác nhận lịch hẹn - %s') % self.name,
                'subject': ('Xác nhận lịch hẹn'),
                'partner_id': self.partner_id.id,
                'phone': self.phone,
                'direction': 'out',
                'company_id': self.company_id.id,
                'crm_id': self.id,
                'country_id': self.country_id.id,
                'street': self.street,
                'care_type': 'DVKH',
                'type_crm_id': self.env.ref('crm_base.type_phone_call_confirm_appointment').id,
                'booking_date': self.booking_date,
                'call_date': self.booking_date.replace(hour=1, minute=0, second=0) - relativedelta(days=1),
            })
        # sinh sms từ bk sinh ra từ đa kênh
        if self.ticket_id:
            script_sms = self.company_id.script_sms_id
            for item in script_sms:
                if item.run:
                    name = ''
                    # gửi SMS xác nhận làm dịch vụ
                    if item.type == 'XNLH':
                        name = 'Xác nhận lịch hẹn - %s' % self.name
                        send_date = datetime.now()
                    # nhắc hẹn khách hàng lần 1
                    elif item.type == 'NHKHL1' and days > 1:
                        name = 'Nhắc hẹn khách hàng lần 1 - %s' % self.name
                        send_date = self.booking_date.replace(hour=2, minute=0, second=0) - relativedelta(days=1)
                    # nhắc hẹn khách hàng lần 2
                    # elif item.type == 'NHKHL2' and days >= 1:
                    #     name = 'Nhắc hẹn khách hàng lần 2 - %s' % self.name
                    #     send_date = self.booking_date - timedelta(hours=1)
                    if name:
                        content_sms = item.content.replace('[Ten_KH]', self.contact_name)
                        content_sms = content_sms.replace('[Ma_Booking]', self.name)
                        content_sms = content_sms.replace('[Booking_Date]', self.booking_date.strftime('%d-%m-%Y'))
                        if self.company_id.code == 'BVHH.HCM.01':
                            company_bv_da = self.env['res.company'].sudo().search([('code', '=', 'DN.HCM.08')], limit=1)
                            if company_bv_da:
                                content_sms = content_sms.replace('[Location_Shop]', company_bv_da.location_shop)
                                content_sms = content_sms.replace('[Ban_Do]', company_bv_da.map_shop)
                            else:
                                content_sms = content_sms.replace('[Location_Shop]', self.company_id.location_shop)
                                content_sms = content_sms.replace('[Ban_Do]', company_bv_da.map_shop)
                        else:
                            content_sms = content_sms.replace('[Location_Shop]', self.company_id.location_shop)
                            content_sms = content_sms.replace('[Ban_Do]', self.company_id.map_shop)
                        if self.company_id.health_declaration:
                            content_sms = content_sms.replace('[Khai_Bao]', self.company_id.health_declaration)
                        crm_sms_vals = []

                        # if item.type == 'XNLH' and item.has_zns:
                        #     # TODO cấu hình trong setting
                        #     # Xác nhận đặt hẹn thành công: 7155
                        #     content_zns = {
                        #         'template_id': 7155,
                        #         'params': {
                        #             "ma_booking": self.name,
                        #             "customer_name": self.contact_name,
                        #             "booking_date": self.booking_date.strftime('%d/%m/%Y')
                        #         }
                        #     }
                        #     zns = {
                        #         'name': name,
                        #         'contact_name': self.contact_name,
                        #         'partner_id': self.partner_id.id,
                        #         'phone': self.phone,
                        #         'company_id': self.company_id.id,
                        #         'company2_id': [(6, 0, self.company2_id.ids)],
                        #         'crm_id': self.id,
                        #         'send_date': send_date,
                        #         'desc': json.dumps(content_zns),
                        #         'type': 'zns',
                        #     }
                        #     crm_sms_vals.append(zns)

                        sms = {
                            'name': name,
                            'contact_name': self.contact_name,
                            'partner_id': self.partner_id.id,
                            'phone': self.phone,
                            'company_id': self.company_id.id,
                            'company2_id': [(6, 0, self.company2_id.ids)],
                            'crm_id': self.id,
                            'send_date': send_date,
                            'desc': content_sms,
                        }
                        crm_sms_vals.append(sms)

                        self.env['crm.sms'].with_user(user.id).sudo().create(crm_sms_vals)

        # sinh sms từ bk tạo tại cơ sở( bk được tạo trong ngày tại cơ sở ko sinh sms)
        else:
            if self.booking_date.date() > time:
                script_sms = self.company_id.script_sms_id
                for item in script_sms:
                    if item.run:
                        name = ''
                        # gửi SMS xác nhận làm dịch vụ
                        if item.type == 'XNLH':
                            name = 'Xác nhận lịch hẹn - %s' % self.name
                            send_date = datetime.now()
                        # nhắc hẹn khách hàng lần 1
                        elif item.type == 'NHKHL1' and days > 1:
                            name = 'Nhắc hẹn khách hàng lần 1 - %s' % self.name
                            send_date = self.booking_date.replace(hour=2, minute=0, second=0) - relativedelta(days=1)
                        # nhắc hẹn khách hàng lần 2
                        # elif item.type == 'NHKHL2' and days >= 1:
                        #     name = 'Nhắc hẹn khách hàng lần 2 - %s' % self.name
                        #     send_date = self.booking_date - timedelta(hours=1)
                        if name:
                            content_sms = item.content.replace('[Ten_KH]', self.contact_name)
                            content_sms = content_sms.replace('[Ma_Booking]', self.name)
                            content_sms = content_sms.replace('[Booking_Date]', self.booking_date.strftime('%d-%m-%Y'))
                            content_sms = content_sms.replace('[Location_Shop]', self.company_id.location_shop)
                            content_sms = content_sms.replace('[Ban_Do]', self.company_id.map_shop)
                            if self.company_id.health_declaration:
                                content_sms = content_sms.replace('[Khai_Bao]', self.company_id.health_declaration)

                            crm_sms_vals = []

                            # if item.type == 'XNLH' and item.has_zns:
                            #     # TODO cấu hình trong setting
                            #     # Xác nhận đặt hẹn thành công: 7155
                            #     content_zns = {
                            #         'template_id': 7155,
                            #         'params': {
                            #             "ma_booking": self.name,
                            #             "customer_name": self.contact_name,
                            #             "booking_date": self.booking_date.strftime('%d/%m/%Y')
                            #         }
                            #     }
                            #     zns = {
                            #         'name': name,
                            #         'contact_name': self.contact_name,
                            #         'partner_id': self.partner_id.id,
                            #         'phone': self.phone,
                            #         'company_id': self.company_id.id,
                            #         'company2_id': [(6, 0, self.company2_id.ids)],
                            #         'crm_id': self.id,
                            #         'send_date': send_date,
                            #         'desc': json.dumps(content_zns),
                            #         'type': 'zns',
                            #     }
                            #     crm_sms_vals.append(zns)
                            sms = {
                                'name': name,
                                'contact_name': self.contact_name,
                                'partner_id': self.partner_id.id,
                                'phone': self.phone,
                                'company_id': self.company_id.id,
                                'company2_id': [(6, 0, self.company2_id.ids)],
                                'crm_id': self.id,
                                'send_date': send_date,
                                'desc': content_sms,
                            }
                            crm_sms_vals.append(sms)
                            self.env['crm.sms'].with_user(user.id).sudo().create(crm_sms_vals)
