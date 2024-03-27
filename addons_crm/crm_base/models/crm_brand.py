from odoo import fields, api, models, _


class CrmBrand(models.Model):
    _name = 'crm.brand'
    _description = 'Crm Brand'

    name = fields.Char('Name')
    company_ids = fields.One2many('res.company', 'brand_id', string='Location')
    code = fields.Char('Code')
    phone = fields.Char('Phone')
    image = fields.Image('Logo brand')
    type = fields.Selection([('hospital', 'Hospital'), ('academy', 'Academy')], string='Type')
    id_brand_insight = fields.Integer('Id brand insight')


class TeamBrand(models.Model):
    _name = 'crm.team.brand'
    _description = 'CRM team brand'

    name = fields.Char('Name team')
    brand_id = fields.Many2one('res.brand', string='Brand')
    active = fields.Boolean('Active', default=True)
    company_ids = fields.Many2many('res.company', string='Company')
    user_ids = fields.Many2many('res.users', string='Member', domain='[("company_ids","=",company_ids)]')

    @api.onchange('brand_id')
    def set_company(self):
        if self.brand_id:
            self.company_ids = [(6, 0, self.brand_id.company_ids.ids)]


