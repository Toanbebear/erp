from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class CrmRuleDebt(models.Model):
    _name = 'crm.rule.debt'
    _description = 'Crm Rule Debt'

    name = fields.Char('Name')
    major = fields.Boolean('Major')
    minor = fields.Boolean('Minor')
    spa = fields.Boolean('Spa')
    laser = fields.Boolean('Laser')
    product = fields.Boolean('Product')
    dentistry = fields.Boolean('Dentistry')
    user_id = fields.Many2many('res.users', string='User')
    max_level = fields.Float('Maximum levels(%)')
    foreign_affair = fields.Boolean('Foreign affair')
    ceiling_price = fields.Monetary('Ceiling price')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id.id)

    @api.constrains('max_level')
    def check_max_level(self):
        for rec in self:
            if rec.max_level > 100 or rec.max_level < 0:
                raise ValidationError(_("The maximum level should be between 0 and 100"))
