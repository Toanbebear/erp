from odoo import models, fields, api
from odoo.tools.profiler import profile
import threading
import time
GENDER = [('male', 'Nam'),
          ('female', 'Nữ'),
          ('transguy', 'Transguy'),
          ('transgirl', 'Transgirl'),
          ('other', 'Khác')]


class CreateBooking(models.TransientModel):
    _name = "create.booking"
    _description = "Tạo Booking từ màn hình checkin"

    def domain_campaign(self):
        return [('campaign_status', '=', '2'), ('brand_id', '=', self.env.company.brand_id.id)]


    checkin_id = fields.Many2one('crm.check.in')
    booking_date = fields.Datetime('Giờ hẹn lịch', default=fields.Datetime.now())
    pricelist_id = fields.Many2one('product.pricelist', string='Bảng giá', tracking=True,
                                   domain="[('type','=','service'),('brand_id','=',brand_id)]")

    company_id = fields.Many2one('res.company', 'Chi nhánh')
    brand_id = fields.Many2one(related='company_id.brand_id', string='Thương hiệu')
    source_id = fields.Many2one('utm.source', 'Nguồn')
    category_source_id = fields.Many2one(related='source_id.category_id', string='Nhóm nguồn')
    campaign_id = fields.Many2one('utm.campaign', 'Chiến dịch', domain=domain_campaign)
    country_id = fields.Many2one('res.country', default=241)
    state_id = fields.Many2one(comodel_name='res.country.state', string='Tỉnh/thành phố',
                               domain="[('country_id', '=', country_id)]")
    district_id = fields.Many2one('res.country.district', string='Quận/huyện', domain="[('state_id', '=', state_id)]")
    street = fields.Char('Địa chỉ chi tiết')
    gender = fields.Selection(GENDER, 'Giới tính')
    birth_date = fields.Date('Ngày sinh')
    year_of_birth = fields.Char('Năm sinh')
    partner_id = fields.Many2one('res.partner')
    name = fields.Char('Họ tên')
    phone = fields.Char('Điện thoại')
    mobile = fields.Char('Điện thoại 2')
    phone_no_3 = fields.Char('Điện thoại 3')
    note = fields.Text('Ghi chú')
    collaborator_id = fields.Many2one('collaborator.collaborator', string='Cộng tác viên', domain="[('source_id', '=', source_id), ('company_id', '=', company_id)]")

    @api.onchange('birth_date')
    def onchange_birthdate(self):
        if self.birth_date:
            self.year_of_birth = self.birth_date.year

    def create_booking(self):
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = self.env['res.partner'].sudo().create({
                'name': self.name,
                'code_customer': self.env['ir.sequence'].next_by_code('res.partner'),
                'customer_classification': '1',
                'phone': self.phone,
                'mobile': self.mobile,
                'phone_no_3': self.phone_no_3,
                'country_id': self.country_id.id,
                'state_id': self.state_id.id,
                'street': self.street,
                'district_id': self.district_id.id,
                'birth_date': self.birth_date,
                'gender': self.gender,
                'year_of_birth': self.year_of_birth,
                'company_id': False,
                'source_id': self.source_id.id
            })
            self.checkin_id.partner = partner.id
        data = {
            'name': self.name,
            'customer_classification': '1',
            'phone': self.phone,
            'mobile': self.mobile,
            'phone_no_3': self.phone_no_3,
            'contact_name': self.name,
            'partner_id': partner.id,
            'code_customer': self.partner_id.code_customer if self.partner_id else False,
            'type_crm_id': self.env.ref('crm_base.type_lead_new').id,
            'gender': self.gender,
            'birth_date': self.birth_date,
            'year_of_birth': self.year_of_birth,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'district_id': self.district_id.id,
            'street': self.street,
            'type': 'lead',
            'type_data_partner': self.partner_id.type_data_partner if self.partner_id else 'new',
            'stage_id': self.env.ref('crm_base.crm_stage_booking').id,
            'company_id': self.company_id.id,
            'brand_id': self.company_id.brand_id.id,
            'price_list_id': self.pricelist_id.id,
            'original_source_id': self.partner_id.source_id.id if self.partner_id else self.source_id.id,
            'source_id': self.source_id.id,
            'category_source_id': self.source_id.category_id.id,
            'campaign_id': self.campaign_id.id,
            'description': self.note,
            'collaborator_id': self.collaborator_id.id if self.collaborator_id else False
        }
        lead_id = self.env['crm.lead'].create(data)
        data.update({
            'type_crm_id': self.env.ref('crm_base.type_oppor_new').id,
            'type': 'opportunity',
            'name': '/',
            'customer_come': 'yes',
            'arrival_date': self.booking_date,
            'booking_date': self.booking_date,
            'lead_id': lead_id.id,
            'stage_id': self.env.ref('crm_base.crm_stage_confirm').id,
        })
        booking = self.env['crm.lead'].create(data)
        booking.stage_id = self.env.ref('crm_base.crm_stage_confirm').id
        self.checkin_id.booking = booking.id

    # def create_booking(self):
    #     if self.partner_id:
    #         partner = self.partner_id
    #     else:
    #         partner = self.env['res.partner'].sudo().create({
    #             'name': self.name,
    #             'code_customer': self.env['ir.sequence'].next_by_code('res.partner'),
    #             'customer_classification': '1',
    #             'phone': self.phone,
    #             'mobile': self.mobile,
    #             'phone_no_3': self.phone_no_3,
    #             'country_id': self.country_id.id,
    #             'state_id': self.state_id.id,
    #             'street': self.street,
    #             'district_id': self.district_id.id,
    #             'birth_date': self.birth_date,
    #             'gender': self.gender,
    #             'year_of_birth': self.year_of_birth,
    #             'company_id': False,
    #             'source_id': self.source_id.id,
    #         })
    #         self.checkin_id.partner = partner.id
    #     data = {
    #         'name': '/',
    #         'customer_classification': '1',
    #         'phone': self.phone,
    #         'mobile': self.mobile,
    #         'phone_no_3': self.phone_no_3,
    #         'contact_name': self.name,
    #         'partner_id': partner.id,
    #         'code_customer': self.partner_id.code_customer if self.partner_id else False,
    #         'type_crm_id': self.env.ref('crm_base.type_oppor_new').id,
    #         'gender': self.gender,
    #         'birth_date': self.birth_date,
    #         'year_of_birth': self.year_of_birth,
    #         'country_id': self.country_id.id,
    #         'state_id': self.state_id.id,
    #         'district_id': self.district_id.id,
    #         'street': self.street,
    #         'type': 'opportunity',
    #         'type_data_partner': self.partner_id.type_data_partner if self.partner_id else 'new',
    #         'stage_id': self.env.ref('crm_base.crm_stage_confirm').id,
    #         'company_id': self.company_id.id,
    #         'brand_id': self.company_id.brand_id.id,
    #         'price_list_id': self.pricelist_id.id,
    #         'original_source_id': self.partner_id.source_id.id if self.partner_id else self.source_id.id,
    #         'source_id': self.source_id.id,
    #         'category_source_id': self.source_id.category_id.id,
    #         'campaign_id': self.campaign_id.id,
    #         'description': self.note,
    #         'customer_come': 'yes',
    #         'arrival_date': self.booking_date
    #     }
    #     booking_id = self.env['crm.lead'].create(data)
    #     self.checkin_id.booking = booking_id.id
    #     self.checkin_id.write({
    #         'name': partner.name,
    #         'date_of_birth': partner.birth_date,
    #         'year_of_birth': partner.birth_date.year,
    #     })
    #     threaded_create_lead = threading.Thread(target=self.create_lead, args=([self.id, booking_id.id, data]))
    #     threaded_create_lead.start()
    #     time.sleep(1)
    #
    # def create_lead(self, checkin, booking, data):
    #     try:
    #         with api.Environment.manage():
    #             new_cr = self.pool.cursor()
    #             self = self.with_env(self.env(cr=new_cr))
    #             print(booking)
    #             booking_id = self.env['crm.lead'].sudo().browse(booking)
    #             data.update({
    #                 'name': self.name,
    #                 'type': 'lead',
    #                 'type_crm_id': self.env.ref('crm_base.type_lead_new').id,
    #                 'stage_id': self.env.ref('crm_base.crm_stage_booking').id,
    #             })
    #             data.pop('arrival_date')
    #             data.pop('customer_come')
    #             lead_id = self.env['crm.lead'].sudo().create(data)
    #             print(lead_id, booking_id)
    #             booking_id.lead_id = lead_id.id
    #     except Exception as e:
    #         print(e)

