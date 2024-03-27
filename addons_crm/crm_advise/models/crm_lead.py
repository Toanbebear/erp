from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'

    advise_ids = fields.One2many('crm.advise.line', 'crm_id', 'Phiếu tư vấn dịch vụ')

    def select_service(self):
        crm_line = self.crm_line_ids.filtered(lambda r: (r.stage == 'chotuvan'))
        if len(crm_line) > 0:
            raise ValidationError('Không thể tạo phiếu khám do trong booking còn dịch vụ ở trạng thái Chờ tư vấn!')
        # if not self.collaborator_id and 'ctv' in self.source_id.name.lower() and self.brand_id.id in (1, 3):
        #     raise ValidationError('Không thể tạo phiếu khám do booking chưa được gán Cộng tác viên.')
        if self.source_id.is_collaborator and not self.collaborator_id and self.brand_id.id in (1, 3):
            raise ValidationError('Không thể tạo phiếu khám do booking chưa được gán Cộng tác viên.')
        return {
            'name': 'Lựa chọn dịch vụ',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_base.view_form_crm_select_service').id,
            'res_model': 'crm.select.service',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_booking_id': self.id,
                'default_height': self.partner_id.height,
                'default_weight': self.partner_id.weight,
                'default_institution': self.env['sh.medical.health.center'].sudo().
                search([('his_company', '=', self.env.company.id)], limit=1).id,
            },
            'target': 'new',
        }

    @api.model
    def create(self, vals):
        if 'partner_id' in vals and 'brand_id' in vals and 'type' in vals and vals['type'] == 'opportunity':
            booking = self.env['crm.lead'].sudo().search(
                [('partner_id', '=', int(vals['partner_id'])), ('effect', '=', 'effect'), ('brand_id', '=', int(vals['brand_id'])), ('type','=','opportunity')], limit=1)
            if booking:
                raise ValidationError(
                    'Hiện tại khách hàng %s có %s đang có hiệu lực.' % (booking.partner_id.name, booking.name))
        return super(CrmLeadInherit, self).create(vals)