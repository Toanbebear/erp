from odoo import models


class QueueSpecialty(models.Model):
    _inherit = "queue.job"
    _order = "id DESC"
