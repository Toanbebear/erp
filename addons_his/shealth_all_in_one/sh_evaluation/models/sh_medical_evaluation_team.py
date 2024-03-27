from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SHealthEvaluationTeam(models.Model):
    _name = "sh.medical.evaluation.team"
    _description = "Evaluation Team"

    # _sql_constraints = [('name_unique', 'unique(name,team_member,role,service_performances)',
    #                      "Vai trò của thành viên phải là duy nhất!")]

    @api.constrains('name', 'team_member', 'service_performances', 'role')
    def _check_constrains_team_member(self):
        for rec in self:
            similars = self.env['sh.medical.evaluation.team'].search(
                [('id', '!=', rec.id), ('name', '=', rec.name.id), ('team_member', '=', rec.team_member.id),
                 ('role', '=', rec.role.id)])
            if similars:
                for sim_rec in similars:
                    for rec_service in rec.service_performances:
                        if rec_service in sim_rec.service_performances:
                            raise ValidationError('Vai trò của thành viên với dịch vụ phải là duy nhất!')

    name = fields.Many2one('sh.medical.evaluation', string='Tái khám')
    team_member = fields.Many2one('sh.medical.physician', string='Thành viên',
                                  help="Health professional that participated on this surgery",
                                  domain=[('is_pharmacist', '=', False)], required=True)

    service_performances = fields.Many2many('sh.medical.health.center.service', 'sh_evaluation_team_services_rel',
                                            'evaluation_team_id', 'service_id', string='Dịch vụ thực hiện',
                                            help="Các dịch vụ của thành viên với vai trog này thực hiện")

    role = fields.Many2one('sh.medical.team.role', string='Vai trò')
    notes = fields.Char(string='Note')
