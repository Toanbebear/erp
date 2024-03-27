from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class AccountPaymentCollaborators(models.Model):
    _inherit = 'account.payment'

    # def post(self):
    #     if self.crm_id:
    #         if not self.crm_id.collaborator_id and 'ctv' in self.crm_id.source_id.name.lower() and self.crm_id.brand_id.id in (1, 3):
    #             raise ValidationError('Không thể tạo phiếu thanh toán do booking chưa được gán Cộng tác viên.')
    #     return super(AccountPaymentCollaborators, self).post()

    def post(self):
        if self.crm_id:
            if self.crm_id.source_id.is_collaborator and not self.crm_id.collaborator_id and self.crm_id.brand_id.id in (1, 3):
                raise ValidationError('Không thể tạo phiếu thanh toán do booking chưa được gán Cộng tác viên.')
        return super(AccountPaymentCollaborators, self).post()

    @api.model
    def create(self, vals):
        if 'crm_id' in vals:
            booking_id = self.env['crm.lead'].sudo().browse(vals['crm_id'])
            if booking_id:
                # if not booking_id.collaborator_id and 'ctv' in booking_id.source_id.name.lower() and booking_id.brand_id.id in (1, 3):
                #     raise ValidationError('Không thể tạo phiếu thanh toán do booking chưa được gán Cộng tác viên.')
                if booking_id.source_id.is_collaborator and not booking_id.collaborator_id and booking_id.brand_id.id in (1, 3):
                    raise ValidationError('Không thể tạo phiếu thanh toán do booking chưa được gán Cộng tác viên.')
        return super(AccountPaymentCollaborators, self).create(vals)

    def write(self, vals):
        if 'crm_id' in vals:
            booking_id = self.env['crm.lead'].sudo().browse(vals['crm_id'])
            if booking_id:
                # if not booking_id.collaborator_id and 'ctv' in booking_id.source_id.name.lower() and booking_id.brand_id.id in (1, 3):
                #     raise ValidationError('Không thể sửa phiếu thanh toán do booking chưa được gán Cộng tác viên.')
                if booking_id.source_id.is_collaborator and not booking_id.collaborator_id and booking_id.brand_id.id in (1, 3):
                    raise ValidationError('Không thể sửa phiếu thanh toán do booking chưa được gán Cộng tác viên.')
        return super(AccountPaymentCollaborators, self).write(vals)
