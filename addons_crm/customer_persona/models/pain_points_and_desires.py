from odoo import fields, models, api


class PainPointsAndDesires(models.Model):
    _name = 'pain.point.and.desires'
    _description = 'Pain Points and Customer Desires'

    partner_id = fields.Many2one('res.partner', string='Partner')
    type = fields.Selection([('pain_point', 'Pain points'), ('desires', 'Desires')], string='Type')
    name = fields.Text('Description')
    solution = fields.Text('Hướng xử lý')
    create_on = fields.Datetime('Create on', default=fields.Datetime.now())
    create_by = fields.Many2one('res.users', string='Create by', default=lambda self: self.env.user)
    department_id = fields.Many2one('hr.department', string='Business unit', tracking=True, compute='set_department',
                                    store=True)
    create_by_department = fields.Char('Phòng ban người tạo', related='department_id.complete_name')

    @api.depends('create_by')
    def set_department(self):
        for rec in self:
            rec.department_id = False
            if rec.create_by:
                rec.department_id = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', rec.create_by.id)]).department_id.id