from odoo import fields, models, api


class SHealthCentersOperatingRooms(models.Model):
    _inherit = 'sh.medical.health.center.ot'
    _description = " Department "

    work_center_id = fields.Char(string='Mã tính giá thành')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
