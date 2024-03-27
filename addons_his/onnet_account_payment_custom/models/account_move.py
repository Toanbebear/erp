# DEALINGS IN THE SOFTWARE.

##############################################################################

from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
# Inherit Payment

class AccountMove(models.Model):
    _inherit = 'account.move'

    x_content_payment = fields.Text(string='Nội dung giao dịch')