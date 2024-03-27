import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class Physician(models.Model):
    _inherit = 'sh.medical.physician'

    def write(self, vals):
        res = super(Physician, self).write(vals)
        for record in self:
            if vals.get('department'):
                print(vals.get('department'))
                print(record.department)
                if record.sh_user_id:
                    room_ids = self.env['sh.medical.health.center.ot'].sudo().search(
                        [('department', 'in', record.department.ids)])
                    record.sh_user_id.room_ids = [(6, 0, room_ids.ids)]
            if vals.get('sh_user_id'):
                user = self.env['res.users'].sudo().search([('id', '=', vals.get('sh_user_id'))])
                if record.department:
                    room_ids = self.env['sh.medical.health.center.ot'].sudo().search(
                        [('department', 'in', record.department.ids)])
                    user.room_ids = [(6, 0, room_ids.ids)]

        return res

    @api.model
    def create(self, vals):
        res = super(Physician, self).create(vals)
        if res.department and res.sh_user_id:
            room_ids = self.env['sh.medical.health.center.ot'].sudo().search([('department', 'in', res.department.ids)])
            res.sh_user_id.room_ids = [(6, 0, room_ids.ids)]
        return res