from odoo import fields, models, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class CreateContractWizard(models.TransientModel):
    _name = 'create.contract.wizard'
    _description = 'Tạo hợp đồng'

    name = fields.Many2one('collaborator.collaborator', string='Cộng tác viên')
    source_id = fields.Many2one('utm.source', string='Nguồn')
    passport = fields.Char('CMTND/CCCD')
    email = fields.Char('Email')
    phone = fields.Char('Điện thoại 1')
    mobile = fields.Char('Điện thoại 2')
    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company', string='Công ty', required=True)
    brand_id = fields.Many2one('res.brand', string='Thương hiệu', )
    bank_id = fields.Many2one('collaborator.bank', 'Tài khoản ngân hàng', domain="[('collaborator_id','=', name)]")

    @api.onchange('brand_id')
    def domain_company_id(self):
        if self.brand_id:
            return {'domain': {'company_id': [('brand_id', '=', self.brand_id.id)]}}
        else:
            return {'domain': {'company_id': []}}

    def create_contract(self):
        check = self.env['collaborator.contract'].search(
            [('state', 'in', ['new', 'confirmed']), ('company_id', '=', self.company_id.ids),
             ('collaborator_id', '=', self.name.ids)])
        if not check:
            contract_id = self.env['collaborator.contract'].create({
                'company_id': self.company_id.id,
                'brand_id': self.brand_id.id,
                'source_id': self.source_id.id,
                'collaborator_id': self.name.id,
                'passport': self.passport,
                'email': self.email,
                'phone': self.phone,
                'mobile': self.mobile,
                'bank_id': self.bank_id.id,
                'end_date': self.create_date + relativedelta(days=365),
            })
            contract_id.check_company_pa_kxd()
            partner = self.env['res.partner'].search([('phone', '=', self.phone)])
            if partner:
                self.name.partner_id = partner.id
            # else:
            #     prt = self.env['res.partner'].create({
            #         'name': self.name.name,
            #         'code_customer': self.env['ir.sequence'].next_by_code('res.partner'),
            #         'aliases': False,
            #         'customer_classification': False,
            #         'overseas_vietnamese': False,
            #         'phone': self.name.phone,
            #         'country_id': self.name.country_id.id,
            #         'state_id': False,
            #         'street': False,
            #         'district_id': False,
            #         'birth_date': False,
            #         'career': False,
            #         'pass_port': self.name.passport,
            #         'pass_port_date': False,
            #         'pass_port_issue_by': False,
            #         'pass_port_address': False,
            #         'gender': False,
            #         'company_id': False,
            #         'source_id': self.name.source_id.id,
            #         'email': self.name.email,
            #         'acc_facebook': False,
            #         'acc_zalo': False,
            #     })
            #     self.name.partner_id = prt.id

            self.name.state = 'new'
            return {
                'name': 'Booking',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('collaborator.collaborator_contract_view_form').id,
                'res_model': 'collaborator.contract',
                'res_id': contract_id.id,
            }
        else:
            for rec in check:
                raise ValidationError(
                    'Bạn không thể tạo hợp đồng, vì đã có hợp đồng trước đó hoặc vẫn đang có hiệu lực' + " " + str(rec.default_code))