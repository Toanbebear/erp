import datetime

from odoo import models, fields, api
from datetime import date, timedelta, datetime
import pytz
from odoo.exceptions import ValidationError
from odoo.tools.misc import profile


class ShWalkin(models.Model):
    _inherit = "sh.medical.appointment.register.walkin"

    not_allow_return = fields.Boolean('Không được phép trả hàng', compute='check_allow_return', help='Không cho phép trả hàng đối với những phiếu MO\nTrue: Không cho trả hàng\nFalse:Cho trả hàng')
    is_invoice = fields.Boolean('Đã tạo invoice', compute='_check_invoice_validate', store=True)

    @api.depends('sale_order_id.invoice_ids')
    def _check_invoice_validate(self):
        for record in self:
            record.is_invoice = False
            if record.sale_order_id and record.create_date >= datetime(2023, 4, 1, 00, 00, 00, 0):
                order = record.sale_order_id
                if order.invoice_ids and ('draft' in order.invoice_ids.mapped('state')):
                    record.is_invoice = True
                elif order.invoice_ids and ('posted' in order.invoice_ids.mapped('state')):
                    record.is_invoice = True

    @api.depends('close_walkin')
    def check_allow_return(self):
        for record in self:
            record.not_allow_return = False
            if record.close_walkin and ((record.close_walkin + timedelta(days=2)) <= date.today()):
                record.not_allow_return = True

    def create_invoice(self):
        time = datetime.now()
        tz_current = pytz.timezone(self._context.get('tz') or 'UTC')  # get timezone user
        tz_database = pytz.timezone('UTC')
        time = tz_database.localize(time)
        time = time.astimezone(tz_current)
        date_check = time.date() - timedelta(days=2)
        start_date = datetime(2023, 3, 31, 17, 00, 00, 00)
        walkin_done = self.env['sh.medical.appointment.register.walkin'].sudo().search([('close_walkin', '<=', date_check), ('state', '=', 'Completed'), ('create_date', '>=', start_date), ('is_invoice', '=', False)], limit=1000)
        for walkin in walkin_done:
            order = walkin.sale_order_id
            # CHECK CÓ TÀI KHOẢN TRÊN PARTNER
            id = order.company_id.id
            a = order.partner_id.with_context(force_company= id).property_account_receivable_id.company_id.id
            if a and a == id:

                if not order.invoice_ids or (('cancel' in order.invoice_ids.mapped('state')) and (len(set(order.invoice_ids.mapped('state'))) == 1)):
                    journal_id = self.env['account.journal'].sudo().search([('company_id', '=', order.company_id.id), ('type', '=', 'sale')])
                    if journal_id:
                        invoice_date = order.date_order
                        if order.invoice_date:
                            invoice_date = order.invoice_date
                        invoice = order.with_context(force_company=order.company_id.id)._create_invoices(journal_id=journal_id.id, invoice_date=invoice_date)
                        invoice.invoice_origin = invoice.invoice_origin + '(DV)'
                        invoice.order_id = order.id
                        if invoice.amount_total == order.amount_total:
                            invoice.with_context(force_company=invoice.company_id.id).action_post()

    def set_to_completed(self):
        res = super(ShWalkin, self).set_to_completed()
        self.sale_order_id.invoice_date = datetime.now()
        return res

    # def set_to_completed(self):
    #     res = super(ShWalkin, self).set_to_completed()
    #     self.sale_order_id.date_order = datetime.datetime.now()
    #     return res


class ShLabTest(models.Model):
    _inherit = "sh.medical.lab.test"

    # not_allow_return = fields.Boolean(related='walkin.not_allow_return')
    not_allow_return = fields.Boolean('Được trả hàng')

    def set_to_test_inprogress(self):
        if self.not_allow_return:
            self.state = 'Test In Progress'
        else:
            return super(ShLabTest, self).set_to_test_inprogress()
        
    def set_to_test_complete(self):
        if self.not_allow_return:
            self.state = 'Completed'
        else:
            return super(ShLabTest, self).set_to_test_complete()


class ShImageTest(models.Model):
    _inherit = "sh.medical.imaging"

    not_allow_return = fields.Boolean(related='walkin.not_allow_return')


class ShSurgery(models.Model):
    _inherit = "sh.medical.surgery"

    not_allow_return = fields.Boolean(related='walkin.not_allow_return')
                
    def action_surgery_start(self):
        if self.not_allow_return:
            self.state = 'In Progress'
        else:
            return super(ShSurgery, self).action_surgery_start()
        
    def action_surgery_end(self):
        if self.not_allow_return:
            self.state = 'Done'
        else:
            return super(ShSurgery, self).action_surgery_end()


class ShSpecialty(models.Model):
    _inherit = "sh.medical.specialty"

    not_allow_return = fields.Boolean(related='walkin.not_allow_return')

    def action_specialty_start(self):
        if self.not_allow_return:
            self.state = 'In Progress'
        else:
            return super(ShSpecialty, self).action_specialty_start()
        
    def action_specialty_end(self):
        if self.not_allow_return:
            self.state = 'Done'
        else:
            res = super(ShSpecialty, self).action_specialty_end()
            return res


class ShPatientRounding(models.Model):
    _inherit = "sh.medical.patient.rounding"

    not_allow_return = fields.Boolean(compute='check_allow_return')

    @api.depends('inpatient_id.walkin')
    def check_allow_return(self):
        for record in self:
            record.not_allow_return = False
            if record.inpatient_id and record.inpatient_id.walkin and not record.inpatient_id.evaluation and record.inpatient_id.walkin.not_allow_return:
                record.not_allow_return = True

    def set_to_draft(self):
        if self.not_allow_return:
            self.state = 'Draft'
        else:
            return super(ShPatientRounding, self).set_to_draft()

    def set_to_completed(self):
        if self.not_allow_return:
            self.state = 'Completed'
        else:
            super(ShPatientRounding, self).set_to_completed()


class ShPrescription(models.Model):
    _inherit = "sh.medical.prescription"

    not_allow_return = fields.Boolean('Không cho trả hàng')
    # not_allow_return = fields.Boolean(compute='check_allow_return')

    # @api.depends('walkin', 'evaluation')
    # def check_allow_return(self):
    #     for record in self:
    #         record.not_allow_return = False
    #         if record.evaluation:
    #             record.not_allow_return = True
    #         elif not record.evaluation and record.walkin and record.walkin.not_allow_return:
    #             record.not_allow_return = True


# class ShEvaluation(models.Model):
#     _inherit = "sh.medical.evaluation"
#
#     close_evaluation = fields.Date('Ngày đóng phiếu')
#     not_allow_return = fields.Boolean('Không được phép trả hàng', compute='check_allow_return')
#
#     @api.depends('walkin', 'walkin.close_walkin', 'state')
#     def check_allow_return(self):
#         for record in self:
#             record.not_allow_return = False
#             if record.state == 'Complete' and record.walkin and record.walkin.close_walkin and (
#                     (record.walkin.close_walkin + timedelta(days=2)).date() >= date.today()):
#                 record.not_allow_return = True
