import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SHMedicalLabTest(models.Model):
    _inherit = 'sh.medical.lab.test'

    enough_results = fields.Boolean('Ghi nhận đủ kết quả', default=False)