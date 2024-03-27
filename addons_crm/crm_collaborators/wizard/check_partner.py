from odoo import fields, models, api
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class CheckPartner(models.TransientModel):
    _name = 'check.partner'
    _description = 'Check Partner'

    name = fields.Many2one('crm.collaborators', string='Tên cộng tác viên')
    source_id = fields.Many2one('utm.source', string='Nguồn',)
    pass_port = fields.Char('CMTND/CCCD ')
    email = fields.Char('Email')
    phone = fields.Char('Điện thoại 1')
    mobile = fields.Char('Điện thoại 2')
    start_date = fields.Datetime('Ngày Tạo hợp đồng', default=lambda self: fields.Datetime.now())
    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company', string='Công ty', required=True,
                                 default=lambda self: self.env.company)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', related='company_id.brand_id', store=True)

    def qualify(self):
        check = self.env['collaborators.contract'].search([('stage', 'in', ['draft', 'new', 'open']), ('company_id', '=', self.company_id.ids), ('collaborators_id', '=', self.name.ids)])
        if not check:
            self.name.check_ctv = True
            collaborators_id = self.env['collaborators.contract'].create({
                'company_id': self.company_id.id,
                'brand_id': self.brand_id.id,
                'category_source_id': self.name.category_source_id.id,
                'source_id': self.source_id.id,
                'collaborators_id': self.name.id,
                'pass_port': self.pass_port,
                'email': self.email,
                'phone': self.phone,
                'mobile': self.mobile,
            })

            partner = self.env['res.partner'].search([('phone', '=', self.phone)])
            if partner:
                self.name.partner_id = partner.id
                customer = partner.id
            else:
                prt = self.env['res.partner'].create({
                    'name': self.name.name,
                    'code_customer': self.env['ir.sequence'].next_by_code('res.partner'),
                    'aliases': False,
                    'customer_classification': False,
                    'overseas_vietnamese': False,
                    'phone': self.name.phone,
                    'country_id': self.name.country_id.id,
                    'state_id': False,
                    'street': False,
                    'district_id': False,
                    'birth_date': False,
                    'career': False,
                    'pass_port': self.name.pass_port,
                    'pass_port_date': False,
                    'pass_port_issue_by': False,
                    'pass_port_address': False,
                    'gender': False,
                    'year_of_birth': False,
                    'company_id': False,
                    'source_id': self.name.source_id.id,
                    'email': self.name.email,
                    'acc_facebook': False,
                    'acc_zalo': False,
                })
                customer = prt.id
                self.name.partner_id = customer

            self.name.state = 'new'
            return {
                'name': 'Booking',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('crm_collaborators.view_form_collaborators_contract').id,
                'res_model': 'collaborators.contract',
                'res_id': collaborators_id.id,
            }
        else:
            for rec in check:
                raise ValidationError('Bạn không thể tạo hợp đồng, vì đã có hợp đồng được tạo trước đó hoặc vẫn đang có hiệu lực' + " " + str(rec.default_code))

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id.brand_id:
            return {
                'domain': {'price_list_id': [('brand_id', '=', self.company_id.brand_id.id)]}
            }

