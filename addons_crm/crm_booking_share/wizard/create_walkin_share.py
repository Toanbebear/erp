from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class WalkinShare(models.TransientModel):
    _name = 'create.walkin.share'
    _description = 'Tạo phiếu khám thuê phòng mổ'

    booking = fields.Many2one('crm.lead', string='Booking')
    partner_walkin = fields.Many2one('res.partner', string='Khách hàng làm dịch vụ')
    partner_so_domain = fields.Many2many('res.partner', compute='get_partner_so')
    partner_so = fields.Many2one('res.partner', string='Khách hàng thuê phòng',
                                 domain="[('id','in',partner_so_domain)]")
    service = fields.Many2one('sh.medical.health.center.service', string='Dịch vụ thuê phòng', domain="[('service_category.is_another_cost', '=',True)]")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary('Số tiền')
    note = fields.Char('Lý do đến khám')
    institution = fields.Many2one('sh.medical.health.center', string='Cơ sở thực hiện')
    exam_room_id = fields.Many2one('sh.medical.health.center.ot', string='Phòng thực hiện',
                                   domain="[('department.type','=','Examination'),('institution','=',institution),('related_department', '!=', False)]")

    @api.onchange('booking')
    def get_institution(self):
        if self.booking:
            self.institution = self.env['sh.medical.health.center'].sudo().search(
                [('his_company', '=', self.env.company.id)])

    @api.onchange('institution')
    def reset_exam(self):
        self.exam_room_id = False

    @api.depends('booking')
    def get_partner_so(self):
        for record in self:
            record.partner_so_domain = False
            # if record.booking and record.booking.company2_id:
            #     record.partner_so_domain = [(6, 0, record.booking.company2_id.mapped('partner_id').ids)]
            if record.booking and record.booking.company_id:
                record.partner_so_domain = [(6, 0, [record.booking.company_id.partner_id.id])]

    def create_walkin_share(self):
        note = 'THUÊ PHÒNG MỔ KH : %s' % self.booking.partner_id.name.upper()
        note_so = 'THUÊ PHÒNG MỔ KH : %s (%s)' % (self.booking.partner_id.name.upper(), self.booking.name)

        # Tao sale order
        so = self.env['sale.order'].create({
            'partner_id': self.partner_so.id,
            'pricelist_id': self.booking.price_list_id.id,  # Todo: Xem có cần tạo bảng giá thuê phòng mổ không
            'company_id': self.env.company.id,
            'booking_id': self.booking.id,
            'campaign_id': self.booking.campaign_id.id,
            'source_id': self.booking.source_id.id,
            'note': note_so,
        })
        self.env['sale.order.line'].create({
            'order_id': so.id,
            'product_id': self.service.product_id.id,
            'product_uom': self.service.product_id.uom_id.id,
            'product_uom_qty': 1,
            'price_unit': self.amount,
        })

        if not self.partner_walkin.is_patient:
            # nếu có thông tin người thân
            if self.booking.fam_ids:
                family_data = []
                for item in self.booking.fam_ids:
                    address = item.partner_id.country_id.name
                    if item.partner_id.state_id:
                        address = item.partner_id.state_id.name + ', ' + address
                    family_data.append((0, 0, {'type_relation': item.type_relation_id.id,
                                               'name': item.member_name,
                                               'phone': item.phone,
                                               'address': address}))
                patient = self.env['sh.medical.patient'].create(
                    {'partner_id': self.partner_walkin.id, 'family': family_data})
            else:
                patient = self.env['sh.medical.patient'].create({'partner_id': self.partner_walkin.id})
        else:
            patient = self.env['sh.medical.patient'].search([('partner_id', '=', self.partner_walkin.id)], limit=1)
        # tạo phiếu đón tiếp
        institution = self.env['sh.medical.health.center'].search([('his_company', '=', self.env.company.id)], limit=1)
        service_room = self.exam_room_id  # phòng khám
        self.env['sh.reception'].create({'patient': patient.id,
                                         'institution': institution.id,
                                         'reason': note,
                                         'service_room': service_room.id,
                                         'booking_id': self.booking.id,
                                         'sale_order_id': so.id,
                                         'type_crm_id': self.booking.type_crm_id.id,
                                         'uom_price': 1})
        return so
