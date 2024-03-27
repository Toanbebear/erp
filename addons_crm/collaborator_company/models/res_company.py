from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    collaborator_passport = fields.Char('số CCCD')
    collaborator_passport_date = fields.Date('Ngày cấp')
    collaborator_passport_issue_by = fields.Char('Nơi cấp')
    collaborator_position = fields.Char('Chức vụ')
    collaborator_date_of_birth = fields.Date('Ngày sinh')
    collaborator_phone = fields.Char('Điện thoại')
    check_collaborator = fields.Selection([('1', 'Cá nhân'), ('2', 'Pháp nhân')], string='Loại hợp đồng', default='2')