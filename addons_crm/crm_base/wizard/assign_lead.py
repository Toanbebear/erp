from odoo import fields, api, models, _


class Assign(models.TransientModel):
    _name = 'crm.assign.data'
    _description = 'Assign'

    @api.model
    def default_get(self, fields):
        record_ids = self._context.get('active_ids')
        result = super(Assign, self).default_get(fields)
        ctx = dict(self.env.context)
        if record_ids:
            if ctx.get('default_type_data') == 'pc':
                pc = self.env['crm.phone.call'].browse(record_ids).ids
                result['phone_call_ids'] = pc

            elif ctx.get('default_type_data') == 'crm':
                crm = self.env['crm.lead'].browse(record_ids).ids
                result['crm_ids'] = crm
        return result

    type_data = fields.Selection([('crm', 'CRM'), ('pc', 'PC')], string='Type data')
    phone_call_ids = fields.Many2many('crm.phone.call', string='Phone call')
    crm_ids = fields.Many2many('crm.lead', string='Lead', domain="[('type','=','lead')]")
    user_id = fields.Many2one('res.users', string='User')
    team_id = fields.Many2one('crm.team.brand', string='Team')
    user_ids = fields.Many2many('res.users', string='List user')
    assign_time = fields.Datetime('Assign time', default=fields.Datetime.now())

    @api.onchange('team_id')
    def get_list_user(self):
        if self.team_id:
            self.user_ids = [(6, 0, self.team_id.user_ids.ids)]
            self.user_id = False

    @api.onchange('user_id')
    def set_team(self):
        if self.user_id:
            self.user_ids = False
            self.team_id = False

    def crm_assign_team(self):
        index = 0
        if self.team_id:
            if self.phone_call_ids:
                for rec in self.phone_call_ids:
                    rec.user_id = self.user_ids[index]
                    index = (index + 1) % len(self.user_ids)
                    rec.assign_time = self.assign_time
            elif self.crm_ids:
                for rec in self.crm_ids:
                    rec.user_id = self.user_ids[index]
                    index = (index + 1) % len(self.user_ids)
                    rec.assign_time = self.assign_time
        elif self.user_id:
            if self.phone_call_ids:
                for rec in self.phone_call_ids:
                    rec.user_id = self.user_id
                    rec.assign_time = self.assign_time
            elif self.crm_ids:
                for rec in self.crm_ids:
                    rec.user_id = self.user_id
                    rec.assign_time = self.assign_time
