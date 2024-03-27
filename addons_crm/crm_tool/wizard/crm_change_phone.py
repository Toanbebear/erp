from odoo import fields, models, _
from odoo.exceptions import UserError


class ChangePhoneWizard(models.TransientModel):
    _name = 'crm.change.phone'
    _description = 'CRM Change Phone Wizard'

    def _default_crm_id(self):
        return self.env.context['active_id']

    crm_id = fields.Many2one('crm.lead', default=_default_crm_id)

    phone = fields.Char('Số điện thoại 1', related='crm_id.phone')
    mobile = fields.Char('Số điện thoại 2', related='crm_id.mobile')

    phone_new = fields.Char('Số điện thoại 1 mới')
    mobile_new = fields.Char('Số điện thoại 2 mới')

    def change_phone_lead(self):
        data = {}
        if self.phone_new or self.mobile_new:
            if self.phone_new:
                data['phone'] = self.phone_new
            if self.mobile_new:
                data['mobile'] = self.mobile_new
            if self.phone_new == self.mobile_new:
                raise UserError(_("Số điện thoại 1 và số điện thoại 2 giống nhau."))
            lead = self.env['crm.lead'].browse(self.env.context.get('active_id'))

            if data:
                lead.write(data)
