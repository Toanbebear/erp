from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class UpdateNoteComplaint(models.TransientModel):
    _name = "update.note.complaint"
    _description = 'Cập nhật thêm tóm tắt tái khám'

    evaluation = fields.Many2one('sh.medical.evaluation', 'Phiếu tái khám')
    name = fields.Text('Thông tin thêm')
    datetime_update = fields.Datetime('Thời gian cập nhật', default=lambda self: fields.Datetime.now())
    user_update = fields.Many2one('res.users', 'Người cập nhật')

    def update_note_complaint(self):
        if not self.evaluation:
            raise ValidationError('Không có phiếu tái khám để cập nhật')
        else:
            text = ' \n' + '-' + (self.datetime_update + timedelta(hours=7)).strftime(
                ' %H:%M:%S Ngày %d tháng %m năm %Y') + ' ( ' + self.user_update.name + ' ) : ' + self.name
            if self.evaluation.notes_complaint:
                self.evaluation.notes_complaint += text
            else:
                self.evaluation.notes_complaint = text
