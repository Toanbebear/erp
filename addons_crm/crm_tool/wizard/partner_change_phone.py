from odoo import fields, models, _
from odoo.exceptions import UserError


class PartnerChangePhoneWizard(models.TransientModel):
    _name = 'partner.change.phone'
    _description = 'Partner Change Phone Wizard'

    def _default_partner_id(self):
        return self.env.context['active_id']

    partner_id = fields.Many2one('res.partner', string="Khách hàng", default=_default_partner_id)

    crm_lead_ids = fields.One2many(related='partner_id.opportunity_ids')
    crm_booking_ids = fields.One2many(related='partner_id.crm_ids')
    crm_phone_call_ids = fields.One2many(related='partner_id.phone_call_ids')
    crm_sms_ids = fields.One2many(related='partner_id.sms_ids')
    # crm_loyalty_card_ids = fields.One2many(related='partner_id.loyalty_card_ids')

    phone = fields.Char('Số điện thoại 1', related='partner_id.phone')

    mobile = fields.Char('Số điện thoại 2', related='partner_id.mobile')

    phone_new = fields.Char('Số điện thoại 1 mới')
    mobile_new = fields.Char('Số điện thoại 2 mới')

    apply_partner = fields.Boolean('Áp dụng trên khách hàng', default=True,
                                   help="Áp dụng đổi số điện thoại trên khách hàng")
    apply_crm_lead = fields.Boolean('Áp dụng trên Lead', default=True, help="Áp dụng đổi số điện thoại trên Lead")
    apply_crm_booking = fields.Boolean('Áp dụng trên booking', default=True,
                                       help="Áp dụng đổi số điện thoại trên Booking")
    apply_phone_call = fields.Boolean('Áp dụng trên phonecall', default=True,
                                      help="Áp dụng đổi số điện thoại trên PhoneCall")
    apply_sms = fields.Boolean('Áp dụng trên sms', default=True, help="Áp dụng đổi số điện thoại trên SMS")
    apply_loyalty_card = fields.Boolean('Áp dụng trên Thẻ thành viên', default=True,
                                        help="Áp dụng đổi số điện thoại trên Thẻ thành viên")
    country_id = fields.Many2one('res.country', string='Quốc gia hiện tại', help="Quốc gia hiện tại",
                                 compute='_compute_partner_id')
    country_id_new = fields.Many2one('res.country', string='Quốc gia mới', help="Áp dụng đổi quốc gia mới")

    def change_phone(self):
        data = {}
        if self.phone_new or self.mobile_new:
            if self.country_id_new:
                data['country_id'] = self.country_id_new.id
            if self.phone_new:
                data['phone'] = self.phone_new
            if self.mobile_new:
                data['mobile'] = self.mobile_new
            if self.phone_new == self.mobile_new:
                raise UserError(_("Số điện thoại 1 và số điện thoại 2 giống nhau."))

            if self.apply_partner and data:
                partner = self.env['res.partner'].browse(self.env.context.get('active_id'))

                if partner:
                    partner.write(data)

            if self.apply_crm_lead:
                leads = self.env['crm.lead'].search([('partner_id', '=', self.partner_id.id), ('type', '=', 'lead')])

                if leads and data:
                    for lead in leads:
                        lead.write(data)

            if self.apply_crm_booking:
                bookings = self.env['crm.lead'].search(
                    [('partner_id', '=', self.partner_id.id), ('type', '=', 'opportunity')])

                if bookings and data:
                    for booking in bookings:
                        booking.write(data)

            if self.apply_phone_call:
                phone_calls = self.env['crm.phone.call'].search([('partner_id', '=', self.partner_id.id)])

                if phone_calls:
                    for phone_call in phone_calls:
                        if self.phone_new:
                            phone_call_data = {
                                'phone': self.phone_new
                            }
                            phone_call.write(phone_call_data)

                        elif self.mobile_new:
                            mobile_data = {
                                'phone': self.mobile_new
                            }
                            phone_call.write(mobile_data)

            if self.apply_sms:
                crm_sms = self.env['crm.sms'].search([('partner_id', '=', self.partner_id.id)])

                if crm_sms:
                    for sms in crm_sms:
                        if self.phone_new:
                            sms_data = {
                                'phone': self.phone_new
                            }
                            sms.write(sms_data)

                        elif self.mobile_new:
                            sms_data = {
                                'phone': self.mobile_new
                            }
                            sms.write(sms_data)

            if self.apply_loyalty_card:
                loyalties = self.env['crm.loyalty.card'].search([('partner_id', '=', self.partner_id.id)])
                if loyalties:
                    for loyalty in loyalties:
                        if self.phone_new and loyalty.phone == self.phone:
                            loyalty_data = {
                                'phone': self.phone_new
                            }
                            loyalty.write(loyalty_data)

                        if self.mobile_new and loyalty.phone == self.mobile:
                            loyalty_data = {
                                'phone': self.mobile_new
                            }
                            loyalty.write(loyalty_data)
