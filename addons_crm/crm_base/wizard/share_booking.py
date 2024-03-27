from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class ShareBooking(models.TransientModel):
    _name = 'share.booking'
    _description = 'Share Booking'

    company_shared_id = fields.Many2one('res.company', string='Chọn chi nhánh')
    booking_id = fields.Many2one('crm.lead', string='Booking')

    def get_company(self):
        if self.booking_id:
            state = self.booking_id.walkin_ids.mapped('state')
            if 'Scheduled' in state:
                raise ValidationError('Bạn không thể share booking nếu có phiếu khám của Booking này chưa hoàn thành')
            else:
                self.booking_id.company2_id = [(4, self.company_shared_id.id)]
                if self.booking_id.lead_id.type_crm_id == self.env.ref('crm_base.type_lead_new'):
                    self.booking_id.lead_id.company2_id = [(4, self.company_shared_id.id)]

            so_ids = self.env['sale.order'].sudo().search([('booking_id', '=', self.booking_id.id)])
            for so in so_ids:
                so.sudo().write({
                    'company_allow_ids': [(4, self.company_shared_id.id)]
                })
