from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def name_get(self):
        result = super(ResPartner, self).name_get()
        if self._context.get('name_collaborator_partner'):
            new_result = []
            for sub_res in result:
                record = self.env['res.partner'].browse(sub_res[0])
                name = '%s' % (record.display_name)
                if record.phone:
                    name += '- %s' % (record.phone)
                else:
                    name += ''
                new_result.append((sub_res[0], name))
            return new_result
        return result

    def create_collaborator(self):
        return {
            'name': 'Tạo CTV',
            'view_mode': 'form',
            'res_model': 'collaborator.collaborator',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('collaborator.collaborator_collaborator_view_form').id,
            'context': {
                'default_phone': self.phone,
                'default_name': self.name,
                'default_mobile': self.mobile,
                'default_email': self.email,
                'default_gender': self.gender,
                'default_date_of_birth': self.birth_date,
                'default_passpost': self.pass_port,
                'default_passpost_date': self.pass_port_date,
                'default_passpost_issue_by': self.pass_port_issue_by,
                'default_country_id': self.country_id,
                'default_state_id': self.state_id,
                'default_district_id': self.district_id,
                'default_address': self.street,
                'default_facebook_acc': self.acc_facebook,
                'default_zalo_id': self.acc_zalo,
                'default_is_partner': True,
                'default_partner_id': self.id
            },
            'target': 'new'
        }
