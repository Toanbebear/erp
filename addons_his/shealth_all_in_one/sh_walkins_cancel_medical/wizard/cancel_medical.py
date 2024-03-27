import datetime

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class CancelMedical(models.TransientModel):
    _name = 'cancel.medical'
    _description = 'huy phieu kham'

    cancel_user = fields.Many2one('res.users', string='Người Hủy' , default=lambda self: self.env.user)
    department_cancel_user = fields.Many2one('hr.department', string='Phòng Ban Người Hủy', compute='set_department')
    note = fields.Char(string="Lý Do Hủy")
    date = fields.Datetime('Ngày Hủy', default=lambda self: fields.Datetime.now())
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu Khám')

    def cancelled(self):
        self.ensure_one()
        if 'Done' in self.walkin_id.surgeries_ids.mapped('state'):
            raise ValidationError('Bạn không thể hủy phiếu khám vì có phiếu PHẪU THUẬT ĐÃ HOÀN THÀNH')
        elif 'Done' in self.walkin_id.specialty_ids.mapped('state'):
            raise ValidationError('Bạn không thể hủy phiếu khám vì có phiếu CHUYÊN KHOA ĐÃ HOÀN THÀNH')
        else:
            #hủy SO liên quan đến phiếu khám
            self.walkin_id.sale_order_id.action_cancel()
            # hủy phiếu thu nháp phiếu liên quan đến phiếu khám
            # self.walkin_id.payment_ids.cancel()
            for payment in self.walkin_id.payment_ids:
                if payment.state == 'draft':
                    payment.cancel()
            # Bỏ phiếu khám ra khỏi phiếu thu
            self.walkin_id.payment_ids.write({'walkin': False})

            # xóa cac phieu lab, imaging lien quan cua phieu kham
            for lab in self.walkin_id.lab_test_ids:
                LabTest = self.walkin_id.env['sh.medical.lab.test'].browse(lab.id)
                if LabTest.state == 'Draft':
                    LabTest.unlink()

            for imaging in self.walkin_id.imaging_ids:
                ImagingTest = self.walkin_id.env['sh.medical.imaging'].browse(imaging.id)
                if ImagingTest.state == 'Draft':
                    ImagingTest.unlink()

            # xóa cac phieu lien quan cua phieu kham
            for surgery in self.walkin_id.surgeries_ids:
                Surgery = self.walkin_id.env['sh.medical.surgery'].browse(surgery.id)
                if Surgery.state == 'Draft':
                    Surgery.unlink()

            for specialty in self.walkin_id.specialty_ids:
                Specialty = self.walkin_id.env['sh.medical.specialty'].browse(specialty.id)
                if Specialty.state == 'Draft':
                    Specialty.unlink()

            for inpatient in self.walkin_id.inpatient_ids:
                Inpatient = self.walkin_id.env['sh.medical.inpatient'].browse(inpatient.id)
                if Inpatient.state == 'Draft':
                    Inpatient.unlink()

            for prescription in self.walkin_id.prescription_ids:
                Prescription = self.walkin_id.env['sh.medical.prescription'].browse(prescription.id)
                if Prescription.state == 'Draft':
                    Prescription.unlink()

            for reexam in self.walkin_id.reexam_ids:
                Reexam = self.walkin_id.env['sh.medical.reexam'].browse(reexam.id)
                if Reexam.state == 'Draft':
                    Reexam.unlink()

            complete_walkin_id = self.walkin_id.env['sh.medical.appointment.register.walkin'].search(
                [('booking_id', '=', self.walkin_id.booking_id.id), ('id', '!=', self.walkin_id.id)])
            if not complete_walkin_id:
                self.walkin_id.booking_id.stage_id = self.walkin_id.env.ref('crm_base.crm_stage_confirm').id
            return self.walkin_id.write({
                'state': 'Cancelled',
                'note_cancel': self.note,
                'cancel_user' : self.cancel_user.id,
                'department_cancel_user' : self.department_cancel_user.id,
                'date_cancel' : self.date,
            })


    # lấy về Phòng ban qua User
    @api.depends('cancel_user')
    def set_department(self):
        for rec in self:
            rec.department_cancel_user = False
            employee = self.env['hr.employee'].search([('user_id', '=',rec.cancel_user.id)])
            if employee:
                rec.department_cancel_user = employee.department_id.id


