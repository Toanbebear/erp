import json

from lxml import etree
from odoo import fields, api, models

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None


class CRMVoucher(models.Model):
    _name = 'crm.voucher'
    _inherit = ['qrcode.mixin']
    _description = 'CRM voucher'

    name = fields.Char('Code')
    voucher_program_id = fields.Many2one('crm.voucher.program', string='Voucher program')
    partner_id = fields.Many2one('res.partner', string='Owner')
    partner2_id = fields.Many2one('res.partner', string='Customer used')
    qr_code = fields.Image('QR code', compute='generate_qr', store=True)
    start_date = fields.Date('Start date', related='voucher_program_id.start_date')
    end_date = fields.Date('End date', related='voucher_program_id.end_date')
    stage_voucher = fields.Selection([('new', 'Mới'), ('active', 'Có hiệu lực'), ('used', 'Đã sử dụng'), ('expire', 'Hết hạn')],
                                     string='Stage')
    active = fields.Boolean('Active', default=True)
    crm_id = fields.Many2one('crm.lead', string='Lead/booking')
    order_id = fields.Many2one('sale.order', string='Sale order')
    brand_id = fields.Many2one('res.brand', string='Brand', related='voucher_program_id.brand_id')
    sell_voucher_id = fields.Many2one('sell.voucher', string='Sell Voucher')
    booking_company = fields.Many2one('res.company', string='Chi nhánh', related='crm_id.company_id', store=True)

    @api.model
    def update_stage_voucher(self):
        self.env.cr.execute(""" UPDATE crm_voucher
                                SET stage_voucher = 'expire'
                                FROM crm_voucher_program
                                WHERE crm_voucher_program.id = crm_voucher.voucher_program_id 
                                    AND crm_voucher.stage_voucher NOT IN ('used', 'expire') 
                                    AND crm_voucher_program.end_date < (CURRENT_DATE at time zone 'utc');""")
        self.env.cr.execute(""" UPDATE crm_voucher
                                SET stage_voucher = 'active'
                                FROM crm_voucher_program
                                WHERE crm_voucher_program.id = crm_voucher.voucher_program_id
                                    AND crm_voucher.stage_voucher = 'new'
                                    AND (CURRENT_DATE at time zone 'utc') >= crm_voucher_program.start_date
                                    AND (CURRENT_DATE at time zone 'utc') <= crm_voucher_program.end_date ;""")

    @api.depends('name')
    def generate_qr(self):
        for rec in self:
            if rec.name:
                rec.qr_code = self.qrcode(rec.name)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(CRMVoucher, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                      submenu=submenu)
        doc = etree.XML(res['arch'])

        if view_type == 'form':
            for node in doc.xpath("//field"):
                node.set("readonly", "True")
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = True
                node.set("modifiers", json.dumps(modifiers))

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
