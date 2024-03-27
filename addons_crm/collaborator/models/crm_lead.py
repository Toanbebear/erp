from odoo import fields, models, api
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    is_ctv = fields.Boolean('Nguồn CTV', related='source_id.is_collaborator')
    # collaborator_ids = fields.One2many('collaborator.lead', 'collaborator_id', string='Cộng tác viên')


    @api.onchange('company_id', 'source_id')
    def onchange_company_id_add_domain_collaborator_id(self):
        if self.company_id and self.source_id:
            self.collaborator_id = False
            domain = [('source_id', '=', self.source_id.id), ('state', '=', 'effect')]
            if "KHÔNG XÁC ĐỊNH" in self.company_id.name:
                domain.append(('brand_id', '=', self.brand_id.id))
            else:
                if self.brand_id.id == 3:
                    domain.append(('company_id', 'in', (self.company_id.id, 36)))
                else:
                    domain.append(('company_id', '=', self.company_id.id))
            return {'domain': {'collaborator_id': domain}}

    collaborator_id = fields.Many2one('collaborator.collaborator',
                                      string="Cộng tác viên",
                                      tracking=True)

    def open_lead(self):
        return {
            'name': 'Open Lead',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('crm.crm_lead_view_form').id,
            'res_model': 'crm.lead',
            'context': {},
        }

    def open_booking(self):
        return {
            'name': 'Open Booking',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('crm_base.crm_lead_form_booking').id,
            'res_model': 'crm.lead',
            'context': {},
        }

    def assign_collaborator_id(self):
        if self.crm_line_ids:
            for crm_line in self.crm_line_ids:
                if crm_line.stage in ('processing', 'done'):
                    raise ValidationError('Có dịch vụ đang ở trạng thái Đang xử trí/Kết thúc không thể gán CTV')
        if self.stage_id in (4, 26):
            raise ValidationError('Booking đang ở trạng thái %s không thể gán CTV' % self.stage_id.name)
        else:
            return {
                'name': 'Thêm Cộng tác viên',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('collaborator.collaborator_crm_lead_form').id,
                'res_model': 'collaborator.crm.lead',
                'context': {'default_crm_id': self.id},
                'target': 'new'
            }

    def assign_collaborator_id_manager(self):
        return {
            'name': 'Thêm Cộng tác viên',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('collaborator.collaborator_crm_lead_form').id,
            'res_model': 'collaborator.crm.lead',
            'context': {'default_crm_id': self.id},
            'target': 'new'
        }

    # def request_deposit(self):
    #     if not self.collaborator_id and 'ctv' in self.source_id.name.lower() and self.brand_id.id in (1, 3):
    #         raise ValidationError('Không thể tạo phiếu thanh toán do booking chưa được gán Cộng tác viên.')
    #     return super(CrmLead, self).request_deposit()

    def request_deposit(self):
        if self.source_id.is_collaborator and not self.collaborator_id and self.brand_id.id in (1, 3):
            raise ValidationError('Không thể tạo phiếu thanh toán do booking chưa được gán Cộng tác viên.')
        return super(CrmLead, self).request_deposit()