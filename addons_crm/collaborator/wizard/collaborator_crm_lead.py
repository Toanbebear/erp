from odoo import fields, models, _
from odoo.exceptions import ValidationError


class CollaboratorCrmLead(models.TransientModel):
    _name = 'collaborator.crm.lead'
    _description = 'Gán CTV vào Booking tạo từ cs'

    crm_id = fields.Many2one('crm.lead')
    company_id = fields.Many2one(related='crm_id.company_id')
    source_id = fields.Many2one(related='crm_id.source_id')
    collaborator = fields.Many2one('collaborator.collaborator', domain="[('company_id', '=', company_id), ('source_id', '=', source_id), ('state', '=', 'effect')]")

    def confirm(self):
        self.crm_id.collaborator_id = self.collaborator
        self.crm_id.lead_id.collaborator_id = self.collaborator
