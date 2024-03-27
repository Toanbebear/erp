from odoo import fields, api, models


class CrmInformationConsultant(models.Model):
    _name = 'crm.information.consultant'
    _description = 'Thông tin tư vấn'

    role = fields.Selection([('doctor','Bác sĩ'), ('recept', 'Lễ tân'), ('support','Trợ thủ')], string='Vai trò')
    user_id = fields.Many2one('res.users', string='Tư vấn viên')
    crm_line_id = fields.Many2one('crm.line', string='Dòng dịch vụ')