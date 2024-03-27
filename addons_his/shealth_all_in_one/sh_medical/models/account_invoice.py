##############################################################################
#    Copyright (C) 2018 sHealth (<http://scigroup.com.vn/>). All Rights Reserved
#    sHealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, sHealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

from odoo import api, SUPERUSER_ID, fields, models, _

class account_invoice(models.Model):
    _inherit = 'account.move'

    patient = fields.Many2one('sh.medical.patient', string='Tên bệnh nhân', help="Tên bệnh nhân")

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount(self):
        super(account_invoice, self)._compute_amount()
        for move in self:
            move.amount_untaxed = (move.amount_untaxed / 1000) * 1000
            move.amount_tax_signed = (move.amount_tax_signed / 1000) * 1000
            move.amount_total = (move.amount_total / 1000) * 1000
            move.amount_total_signed = (move.amount_total_signed / 1000) * 1000
            move.amount_residual = (move.amount_residual / 1000) * 1000
            move.amount_residual_signed = (move.amount_residual_signed / 1000) * 1000

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
