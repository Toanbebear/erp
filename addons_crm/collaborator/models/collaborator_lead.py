from odoo import fields, models


class CollaboratorLead(models.Model):
    _name = 'collaborator.lead'
    _description = 'Lead cộng tác viên'

    collaborator_id = fields.Many2one('collaborator.collaborator', string='Cộng tác viên', required=True)
    lead_id = fields.Many2one('crm.lead', string='Lead')

    partner_id = fields.Many2one(related='lead_id.partner_id')
    phone = fields.Char('Số điện thoại', related='lead_id.phone')
    source_id = fields.Many2one('utm.source', 'Nguồn', related='lead_id.source_id')
    company_id = fields.Many2one(related='lead_id.company_id')
    stage_id = fields.Many2one(related='lead_id.stage_id')
    name = fields.Char('Tên khách hàng', related='lead_id.contact_name')
