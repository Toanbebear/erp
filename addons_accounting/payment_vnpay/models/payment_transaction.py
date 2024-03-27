from odoo import fields, models, api
import re
import time


class VNPayTxSips(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _compute_reference(self, values=None, prefix=None):
        res = super(VNPayTxSips, self)._compute_reference(values=values, prefix=prefix)
        acquirer = self.env['payment.acquirer'].browse(values.get('acquirer_id'))
        if acquirer and acquirer.provider == 'vnpay':
            return 'VNPay' + '-' + str(int(time.time()))
        return res
