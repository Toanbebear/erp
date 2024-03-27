from odoo import fields, models, api


class HobbiesAndInterests(models.Model):
    _name = 'hobbies.interest'
    _description = 'Hobbies and Interests'
    _rec_name = 'desc'

    name = fields.Char('Hobbies and Interests', required=True)
    hobbies_parent = fields.Many2one('hobbies.interest', string='Parent Hobbies and Interests')
    desc = fields.Char('Description')

    @api.model
    def create(self, vals_list):
        res = super(HobbiesAndInterests, self).create(vals_list)
        if res.name and res.hobbies_parent:
            res.desc = '%s - %s' % (res.hobbies_parent.name, res.name)
        else:
            res.desc = '%s' % res.name
        return res

    def write(self, vals):
        res = super(HobbiesAndInterests, self).write(vals)
        for record in self:
            if vals.get('name') or vals.get('hobbies_parent'):
                record.desc = '%s - %s' % (record.hobbies_parent.name, record.name)
        return res
