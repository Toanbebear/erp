from odoo import fields, models, api


class CrmCollaborators(models.Model):
    _inherit = 'crm.collaborators'

    ehc_source_id = fields.Many2one('utm.source', string='Nguồn ERP', domain="[('category_id','=',ehc_category_source_id), ('brand_id.code','=', 'HH')]")