import datetime

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class CancelProductsDiscount(models.TransientModel):
    _name = 'cancel.products.discount'
    _description = 'Hủy loại hợp đồng'

    contract_id = fields.Many2one('products.discount', string='Loại hợp đồng')
    REASON_LINE_CANCEL = [('create_wrong', 'Thao tác tạo sai loại hợp đồng'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy')
    note = fields.Text('Ghi chú')

    def cancel_products_discount(self):
        self.contract_id.state = 'cancel'
        self.contract_id.reason_line_cancel = self.reason_line_cancel
        self.contract_id.note = self.note
        self.contract_id.cancel = True
        self.contract_id.cancel_user = self.env.user
        self.contract_id.cancel_date = datetime.datetime.now()


class CancelCollaboratorsContract(models.TransientModel):
    _name = 'cancel.collaborators.contract'
    _description = 'Hủy hợp đồng'

    crm_line_id = fields.Many2one('collaborators.contract', string='Hợp đồng')
    REASON_LINE_CANCEL = [('create_wrong_service', 'Thao tác tạo sai hợp đồng'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy hợp đồng')
    note = fields.Text('Ghi chú')

    def cancel_contract(self):
        self.crm_line_id.stage = 'cancel'
        self.crm_line_id.reason_line_cancel = self.reason_line_cancel
        self.crm_line_id.note = self.note
        self.crm_line_id.cancel = True
        self.crm_line_id.cancel_user = self.env.user
        self.crm_line_id.cancel_date = datetime.datetime.now()

class CancelCollaborators(models.TransientModel):
    _name = 'cancel.collaborators'
    _description = 'Hủy CTV'

    crm_collaborators = fields.Many2one('crm.collaborators', string='Cộng tác viên')
    REASON_LINE_CANCEL = [('create_wrong', 'Thao tác tạo sai Cộng Tác Viên'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy')
    note = fields.Text('Ghi chú')

    @api.onchange('reason_line_cancel')
    def _get_note(self):
        note_mapping = {key: value for key, value in self.REASON_LINE_CANCEL}
        if self.reason_line_cancel == 'create_wrong':
            self.note = note_mapping.get(self.reason_line_cancel)
        else:
            self.note = False

    def cancel_contract(self):
        contract = self.env['collaborators.contract'].search([('stage', 'in', ('open', 'new')), ('collaborators_id', '=', self.crm_collaborators.id)])
        if not contract:
            self.crm_collaborators.state = 'cancel'
            self.crm_collaborators.cancel_note = self.note
        else:
            raise ValidationError('Vẫn còn hợp đồng có hiệu lực bạn không thể hủy')

