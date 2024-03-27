from odoo import models


class SpecialtyTool(models.Model):
    _inherit = "sh.medical.specialty"

    def state_done(self):
        self.state = 'Done'


class SurgeryTool(models.Model):
    _inherit = "sh.medical.surgery"

    def state_done(self):
        self.state = 'Done'


class EvaluationTool(models.Model):
    _inherit = "sh.medical.evaluation"

    def state_done(self):
        self.state = 'Completed'
