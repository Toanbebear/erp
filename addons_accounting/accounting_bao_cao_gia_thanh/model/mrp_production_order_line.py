import json

from odoo import fields, models, api


class ShMedicalSpecialtySupply(models.Model):
    _name = 'sh.medical.specialty.supply'
    _inherit = ['sh.medical.specialty.supply', 'product.cost.mrp.production.material']

    @api.depends('name', 'services', 'qty_used')
    def _compute_bom_ids(self):
        for record in self:
            bom_ids, service_price_ratio = record.seperate_actual_price(record.name, record.services, record.qty_used, 'Specialty')

            record.bom_ids = bom_ids
            record.service_price_ratio = service_price_ratio


class ShMedicalSurgerySupply(models.Model):
    _name = 'sh.medical.surgery.supply'
    _inherit = ['sh.medical.surgery.supply', 'product.cost.mrp.production.material']

    @api.depends('name', 'services', 'qty_used')
    def _compute_bom_ids(self):
        for record in self:
            bom_ids, service_price_ratio = record.seperate_actual_price(record.name, record.services, record.qty_used, 'Surgery')

            record.bom_ids = bom_ids
            record.service_price_ratio = service_price_ratio


class ShMedicalPatientRoundingMedicines(models.Model):
    _name = 'sh.medical.patient.rounding.medicines'
    _inherit = ['sh.medical.patient.rounding.medicines', 'product.cost.mrp.production.material']

    @api.depends('name', 'services', 'qty')
    def _compute_bom_ids(self):
        for record in self:
            bom_ids, service_price_ratio = record.seperate_actual_price(record.name, record.services, record.qty, 'Inpatient')

            record.bom_ids = bom_ids
            record.service_price_ratio = service_price_ratio


class ShMedicalPrescriptionLine(models.Model):
    _name = 'sh.medical.prescription.line'
    _inherit = ['sh.medical.prescription.line', 'product.cost.mrp.production.material']

    @api.depends('name', 'services', 'qty')
    def _compute_bom_ids(self):
        for record in self:
            bom_ids, service_price_ratio = record.seperate_actual_price(record.prescription_id, record.services, record.qty, 'Medicine')

            record.bom_ids = bom_ids
            record.service_price_ratio = service_price_ratio


class ShMedicalLabTestMaterial(models.Model):
    _name = 'sh.medical.lab.test.material'
    _inherit = ['sh.medical.lab.test.material', 'product.cost.mrp.production.material']

    @api.depends('lab_test_id', 'product_id', 'services', 'quantity')
    def _compute_bom_ids(self):
        for record in self:
            bom_ids, service_price_ratio = record.seperate_actual_price(record.lab_test_id, record.services, record.quantity, 'LabTest')

            record.bom_ids = bom_ids
            record.service_price_ratio = service_price_ratio


