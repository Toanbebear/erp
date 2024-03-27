from odoo import fields, models, api, _


class ShMedicalSurgeryTeam(models.Model):
    _inherit = 'sh.medical.surgery.team'

    service_text = fields.Char('Dịch vụ thực hiện', compute='get_service_text')
    is_doctor = fields.Boolean('Vai trò là bác sĩ', compute='get_is_doctor')

    @api.depends('service_performances')
    def get_service_text(self):
        for rec in self:
            list_service = ''
            for service in rec.service_performances:
                list_service += ' | ' + service.name if list_service else service.name
            rec.service_text = list_service

    @api.depends('role')
    def get_is_doctor(self):
        for rec in self:
            if rec.role.id in tuple(map(int, self.env['ir.config_parameter'].sudo().get_param('doctor_surgery_ids').split(', '))):
                rec.is_doctor = True
            else:
                rec.is_doctor = False


class ShMedicalSpecialtyTeam(models.Model):
    _inherit = 'sh.medical.specialty.team'

    service_text = fields.Char('Dịch vụ thực hiện', compute='get_service_text')
    is_doctor = fields.Boolean('Vai trò là bác sĩ', compute='get_is_doctor')

    @api.depends('service_performances')
    def get_service_text(self):
        for rec in self:
            list_service = ''
            for service in rec.service_performances:
                list_service += ' | ' + service.name if list_service else service.name
            rec.service_text = list_service

    @api.depends('role')
    def get_is_doctor(self):
        for rec in self:
            if rec.role.id in tuple(map(int, self.env['ir.config_parameter'].sudo().get_param('doctor_specialty_ids').split(', '))):
                rec.is_doctor = True
            else:
                rec.is_doctor = False
