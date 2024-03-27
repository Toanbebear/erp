from odoo import fields, api, models, _


class TypeRelative(models.Model):
    _name = 'type.relative'
    _description = 'Relation'
    _rec_name = 'desc'

    name = fields.Char('Name', translate=True)
    symmetry_relative = fields.Many2one('type.relative', string='Quan hệ đối xứng')
    desc = fields.Char('Desc')

    @api.model
    def create(self, vals_list):
        res = super(TypeRelative, self).create(vals_list)
        if res.name and res.symmetry_relative:
            res.desc = '%s - %s' % (res.name, res.symmetry_relative.name)
        else:
            res.desc = '%s' % res.name
        return res

    def write(self, vals):
        res = super(TypeRelative, self).write(vals)
        for record in self:
            if vals.get('name') or vals.get('symmetry_relative'):
                if (not record.symmetry_relative) and record.name:
                    record.desc = '%s' % record.name
                else:
                    record.desc = '%s - %s' % (record.name, record.symmetry_relative.name)
        return res


class RelationPartner(models.Model):
    _name = 'relation.partner'
    _description = 'Relation partner'

    name = fields.Char('Name', compute='relatives_get_name', store=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    partner_relative_name = fields.Char('Relatives name')
    partner_relative_id = fields.Many2one('res.partner', string='Account Relatives', compute='get_partner_relative_id',
                                          store=True)
    country_id = fields.Many2one('res.country', string='Country', default=241)
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=', country_id)]")
    street = fields.Char('Street')
    type_relative_id = fields.Many2one('type.relative', string='Relative')
    birth_date = fields.Date('Birth date')
    pass_port = fields.Char('Pass port')
    phone = fields.Char('Phone')
    company_id = fields.Many2one('res.company', string='Company')

    @api.depends('partner_id', 'partner_relative_id', 'type_relative_id')
    def relatives_get_name(self):
        for rec in self:
            if rec.type_relative_id and rec.partner_id and rec.partner_relative_id:
                rec.partner_relative_name = rec.partner_relative_id.name
                rec.name = (_('%s là %s của %s ')) % (
                    rec.partner_relative_name, rec.type_relative_id.name, rec.partner_id.name)

    @api.depends('phone')
    def get_partner_relative_id(self):
        for record in self:
            if record.phone:
                partner = self.env['res.partner'].search([('phone', '=', record.phone)])
                if partner:
                    record.partner_relative_id = partner.id
                    record.partner_relative_name = partner.name

    @api.model
    def create(self, vals):
        relation = super(RelationPartner, self).create(vals)
        if vals.get('phone'):
            if relation.partner_id not in relation.partner_relative_id.relation_ids.mapped('partner_relative_id'):
                relation.partner_relative_id.relation_ids.create({
                    'phone': relation.partner_id.phone,
                    'partner_relative_name': relation.partner_id.name,
                    'partner_id': relation.partner_relative_id.id,
                    'type_relative_id': relation.type_relative_id.id
                })
        return relation

    def write(self, vals):
        for record in self:
            if vals.get('phone'):
                phone_new = vals.get('phone')
                partner = self.env['res.partner'].search([('phone', '=', phone_new)])
                if partner and partner != record.partner_relative_id:
                    relation = record.partner_relative_id.relation_ids.filtered(
                        lambda l: l.partner_relative_id == record.partner_id)
                    relation.unlink()
                res = super(RelationPartner, self).write(vals)
                record.partner_relative_id.relation_ids.create({
                    'phone': record.partner_id.phone,
                    'partner_relative_name': relation.partner_id.name,
                    'partner_id': record.partner_relative_id.id,
                    'type_relative_id': record.type_relative_id.id
                })
                return res
