from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    content_complain_ids = fields.One2many('crm.content.complain', 'partner_id', string='Nội dung khiếu nại')
    sale_order_line_ids = fields.One2many('sale.order.line', 'partner_id', string='Sản phẩm bán')
    advice_ids = fields.One2many('crm.advise.line', 'partner_id', string='Dịch vụ tiềm năng', domain=[('is_potential', '=', True)])
    surgery_ids = fields.One2many('sh.medical.surgery', 'partner_id', string='Phiếu PT-TT')
    specialty_ids = fields.One2many('sh.medical.specialty', 'partner_id', string='Phiếu CK')
    year_of_birth = fields.Char('Year of birth', tracking=True, compute='set_year_of_birth', store=True)
    sale_order_ids = fields.One2many('sale.order', 'partner_id', string='Sales Order', domain=[('pricelist_type', '=', 'product')])
    phone_call_ids = fields.One2many('crm.phone.call', 'partner_id', string='Phonecall', domain=[('call_date', '<=', fields.Datetime.now())])
    phone_call_ids_new = fields.One2many('crm.phone.call', 'partner_id', string='Phonecall', domain=[('call_date', '>', fields.Datetime.now())])


    @api.depends('birth_date')
    def set_year_of_birth(self):
        for rec in self:
            if rec.birth_date:
                rec.year_of_birth = int(rec.birth_date.year)

    def button_show_qr(self):
        return {
            'name': 'Hiển thị QR',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_kangnam_extend.show_qr_booking_form_view').id,
            'res_model': 'show.qr.booking',
            'context': {'default_qr_code_id': self.qr_id,
                        'default_partner_name': self.name},
            'target': 'new',
        }

    def open_image_customer(self):
        if self.env.company and self.env.company.url_image:
            url = self.env.company.url_image + '/%s' % (self.code_customer)
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }
        else:
            raise ValidationError('Công ty chưa được cấu hình. Liên hệ với IT để cấu hình cho công ty của bạn')
