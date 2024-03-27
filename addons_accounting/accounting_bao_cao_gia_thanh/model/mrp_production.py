from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from .constant import MRP_PRODUCTION_STATE


class ShMedicalSpeciality(models.Model):
    _name = 'sh.medical.specialty'
    _inherit = ['sh.medical.specialty', 'product.cost.mrp.production']

    production_cost_line_ids = fields.One2many("tas.mrp.production.cost.line", "mrp_production_id", string="Cost Lines")

    # def action_specialty_end(self):
    #     super(ShMedicalSpeciality, self).action_specialty_end()
    #     for record in self:
    #         if record.state.lower() == 'done':
    #             record.compute_cost_line()
    #             if len(record.production_cost_line_ids) > 0:
    #                 record.generate_journal_entry()


class ShMedicalSurgery(models.Model):
    _name = 'sh.medical.surgery'
    _inherit = ['sh.medical.surgery', 'product.cost.mrp.production']

    production_cost_line_ids = fields.One2many("tas.mrp.production.cost.line", "mrp_production_surgery_id", string="Cost Lines")

    # def action_surgery_end(self):
    #     super(ShMedicalSurgery, self).action_surgery_end()
    #     for record in self:
    #         if record.state.lower() == 'done':
    #             record.compute_cost_line()
    #             if len(record.production_cost_line_ids) > 0:
    #                 record.generate_journal_entry()


class ShMedicalPatientRounding(models.Model):
    _name = 'sh.medical.patient.rounding'
    _inherit = ['sh.medical.patient.rounding', 'product.cost.mrp.production']

    booking_id = fields.Many2one('crm.lead', store=True, compute='_compute_booking_id')
    production_cost_line_ids = fields.One2many("tas.mrp.production.cost.line", "mrp_production_patient_id",
                                               string="Cost Lines")
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', related='inpatient_id.walkin', store=True)

    @api.depends('inpatient_id.walkin')
    def _compute_booking_id(self):
        for record in self:
            booking_id = False
            if record.inpatient_id and record.inpatient_id.walkin:
                booking_id = record.inpatient_id.walkin.booking_id.id
            record.booking_id = booking_id

    # def set_to_completed(self):
    #     super(ShMedicalPatientRounding, self).set_to_completed()
    #     for record in self:
    #         if record.state.lower() == 'done':
    #             record.compute_cost_line()
    #             if len(record.production_cost_line_ids) > 0:
    #                 record.generate_journal_entry()


class ShMedicalPrescription(models.Model):
    _name = 'sh.medical.prescription'
    _inherit = ['sh.medical.prescription', 'product.cost.mrp.production']

    booking_id = fields.Many2one('crm.lead', related='walkin.booking_id', store=True)
    production_cost_line_ids = fields.One2many("tas.mrp.production.cost.line", "mrp_production_prescription_id",
                                               string="Cost Lines")

    # def action_prescription_out(self):
    #     super(ShMedicalPrescription, self).action_prescription_out()
    #     for record in self:
    #         if record.state == 'Đã xuất thuốc':
    #             record.compute_cost_line()
    #             if len(record.production_cost_line_ids) > 0:
    #                 record.generate_journal_entry()


class ShMedicalLabTest(models.Model):
    _name = 'sh.medical.lab.test'
    _inherit = ['sh.medical.lab.test', 'product.cost.mrp.production']

    other_bom = fields.Many2many('sh.medical.lab.bom', string='Bom vật tư')
    production_cost_line_ids = fields.One2many("tas.mrp.production.cost.line", "mrp_production_lab_test_id",
                                               string="Cost Lines")
    booking_id = fields.Many2one('crm.lead', related='walkin.booking_id', store=True)

    # def set_to_test_complete(self):
    #     super(ShMedicalLabTest, self).set_to_test_complete()
    #     for record in self:
    #         if record.state.lower() == 'completed':
    #             record.compute_cost_line()
    #             if len(record.production_cost_line_ids) > 0:
    #                 record.generate_journal_entry()


class WalkinLabtestsResult(models.TransientModel):
    _inherit = 'walkin.labtest.result'

    @api.model
    def create(self, vals):
        result = super(WalkinLabtestsResult, self).create(vals)

        walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.env.context.get('active_id'))
        current_institution = self.env['sh.medical.health.center'].search([('his_company', '=', self.env.companies.ids[0])], limit=1)
        first_lab = True
        for lab_test in walkin.lab_test_ids:
            # set bom for lab test
            test_vals = {
                'other_bom': vals.get('other_bom')
            }
            lab_test.write(test_vals)
        return result

