from odoo import fields,api,models

class CrmSmsInherit(models.Model):

    _inherit = 'crm.sms'

    phone_x = fields.Char('Điện thoại', compute='set_phone_x', store=False)

    @api.depends('phone')
    def set_phone_x(self):
        for rec in self:
            if rec.phone:
                rec.phone_x = rec.phone[0:3] + 'xxxx' + rec.phone[7:]
            else:
                rec.phone_x = False
