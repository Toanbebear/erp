from odoo import models, fields
from odoo.exceptions import ValidationError


class CrmPhoneCallHistory(models.Model):
    _name = 'crm.phone.call.history'
    _description = 'Lịch sử phone call'

    call_id = fields.Char('Call id')
    ticket_id = fields.Char('Ticket id')
    phone_call_id = fields.Many2one('crm.phone.call', 'Phone call')
    res_id = fields.Integer('ID')
    res_model = fields.Char("Model")

    def view_phone_call_cs(self):
        """ Open the website page with the survey form """
        self.ensure_one()
        if self.ticket_id:
            config = self.env['ir.config_parameter'].sudo()
            key = 'domain_caresoft_%s' % self.phone_call_id.brand_id.code.lower()
            domain = config.get_param(key)
            domain = domain.replace('api', 'web55')
            domain = domain + '#/index?type=ticket&id=%s' % self.ticket_id
            return {
                'type': 'ir.actions.act_url',
                'name': "Open ticket",
                'target': 'new',
                'url': domain
            }


class CrmPhoneCallInherit(models.Model):
    _inherit = 'crm.phone.call'

    phone_call_history_ids = fields.One2many('crm.phone.call.history', 'phone_call_id', string='Lịch sử phone call')
