from calendar import monthrange
from datetime import date, datetime

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError

GENDER = [('male', 'Nam'),
          ('female', 'Nữ'),
          ('transguy', 'Transguy'),
          ('transgirl', 'Transgirl'),
          ('other', 'Khác')]


class CollaboratorReportPayment(models.TransientModel):
    _name = 'collaborator.collaborator.create.lead'
    _description = 'Tạo lead từ CTV'

    # def domain_company(self):
    #     if self._context.get('default_collaborator_id'):
    #         contract_ids = self.env['collaborator.contract'].sudo().search([('collaborator_id', '=', self._context.get('default_collaborator_id')), ('state', '=', 'effect')])
    #         return [('id', 'in', contract_ids.company_id.ids)]

    phone = fields.Char('Điện thoại')
    name = fields.Char('Tên khách')
    partner_id = fields.Many2one('res.partner')
    gender = fields.Selection(GENDER, string='Giới tính')
    country_id = fields.Many2one('res.country', string='Quốc gia', default=241)
    stage_id = fields.Many2one('crm.stage', string='Trạng thái', default=5)
    # source_id = fields.Many2one('utm.source', 'Nguồn')
    # company_id = fields.Many2one('res.company', string='Chi nhánh', domain=domain_company)
    company_id = fields.Many2one('res.company', string='Chi nhánh')
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id')
    # price_list_id = fields.Many2one('product.pricelist', string='Bảng giá',
    #                                 domain="[('type','=','service'),('brand_id','=',brand_id),('active','=',True)]", default=False)
    birth_date = fields.Date('Ngày sinh')
    price_list_id = fields.Many2one('product.pricelist', string='Bảng giá')
    check_company_kxd_pa = fields.Boolean('Công ty kxd', default=False)

    @api.onchange('brand_id')
    def domain_price_list_id(self):
        domain = []
        if self.brand_id:
            domain = [('type', '=', 'service'), ('brand_id', '=', self.brand_id.id), ('active', '=', True)]
        return {'domain': {'price_list_id': domain}}

    @api.onchange('brand_id')
    def domain_company_id(self):
        if self.brand_id:
            return {'domain': {'company_id': [('brand_id', '=', self.brand_id.id)]}}
        else:
            return {'domain': {'company_id': []}}
    @api.onchange('phone')
    def check_partner(self):
        if self.phone:
            if self.phone.isdigit() is False:
                raise ValidationError('Điện thoại 1 khách hàng chỉ nhận giá trị số')
            partner = self.env['res.partner'].search([('phone', '=', self.phone)])
            lead_ids = self.env['crm.lead'].search(
                [('phone', '=', self.phone), ('brand_id', '=', self.brand_id.id)], order="id asc", limit=1)
            if partner:
                self.partner_id = partner.id
                self.name = partner.name
                self.gender = partner.gender
                self.country_id = partner.country_id.id
                self.birth_date = partner.birth_date
            else:
                self.partner_id = False
                self.name = lead_ids.contact_name
                self.gender = lead_ids.gender
                self.country_id = lead_ids.country_id.id if lead_ids else self.country_id
                self.birth_date = lead_ids.birth_date

    # @api.onchange('company_id')
    # def get_price_list(self):
    #     if self.company_id:
    #         price_list_id = self.env['product.pricelist'].sudo().search(
    #             [('brand_id', '=', self.company_id.brand_id.id)], limit=1)
    #         if price_list_id:
    #             self.price_list_id = price_list_id.id

    def create_lead(self):
        lead_ids = self.env['crm.lead'].search(
            [('phone', '=', self.phone), ('brand_id', '=', self.brand_id.id)], order="id asc", limit=1)
        if self.partner_id:
            data_lead = {
                'partner_id': self.partner_id.id,
                'customer_classification': self.partner_id.customer_classification,
                'phone': self.partner_id.phone,
                'mobile': self.partner_id.mobile,
                'phone_no_3': self.partner_id.phone_no_3,
                'aliases': self.partner_id.aliases,
                'gender': self.partner_id.gender,
                'birth_date': self.partner_id.birth_date,
                'overseas_vietnamese': self.partner_id.overseas_vietnamese,
                'country_id': self.partner_id.country_id.id,
                'state_id': self.partner_id.state_id.id,
                'district_id': self.partner_id.district_id.id,
                'ward_id': self.partner_id.ward_id.id,
                'street': self.partner_id.street,
                'career': self.partner_id.career,
                'year_of_birth': self.partner_id.year_of_birth,
                'pass_port': self.partner_id.pass_port,
                'pass_port_date': self.partner_id.pass_port_date,
                'pass_port_issue_by': self.partner_id.pass_port_issue_by,
                'pass_port_address': self.partner_id.pass_port_address,
                'name': self.partner_id.name,
                'company_id': self.company_id.id,
                'brand_id': self.brand_id.id,
                'price_list_id': self.price_list_id.id,
                'stage_id': self.stage_id.id,
                'type': 'lead',
                'type_data': 'old',
                'source_id': self.env['collaborator.collaborator'].sudo().browse(
                    self._context.get('default_collaborator_id')).source_id.id,
                'category_source_id': self.env['collaborator.collaborator'].sudo().browse(
                    self._context.get('default_collaborator_id')).source_id.category_id.id,
                'collaborator_id':self._context.get('default_collaborator_id'),
                'type_price_list': 'service'
            }
        else:
            data_lead = {
                'partner_id': False,
                'name': self.name,
                'phone': self.phone,
                'mobile': lead_ids.mobile,
                'phone_no_3': lead_ids.phone_no_3,
                'gender': self.gender,
                'birth_date': self.birth_date,
                'country_id': self.country_id.id,
                'state_id': lead_ids.state_id.id if lead_ids and lead_ids.state_id else False,
                'street': lead_ids.street,
                'customer_classification': lead_ids.customer_classification if lead_ids else "1",
                'year_of_birth': lead_ids.year_of_birth,
                'career': lead_ids.career,
                'pass_port': lead_ids.pass_port,
                'contact_name': self.name,
                'aliases': lead_ids.aliases,
                'source_id': self.env['collaborator.collaborator'].sudo().browse(
                    self._context.get('default_collaborator_id')).source_id.id,
                'type_data': 'new',
                'category_source_id': self.env['collaborator.collaborator'].sudo().browse(
                    self._context.get('default_collaborator_id')).source_id.category_id.id,
                'email_from': lead_ids.email_from,
                'type': 'lead',
                'facebook_acc': lead_ids.facebook_acc,
                'company_id': self.company_id.id,
                'brand_id': self.brand_id.id,
                'price_list_id': self.price_list_id.id,
                'stage_id': self.stage_id.id,
                'collaborator_id': self._context.get('default_collaborator_id'),
                'type_price_list': 'service'
            }
        lead = self.env['crm.lead'].sudo().create(data_lead)

