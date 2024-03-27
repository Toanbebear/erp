from odoo import fields, api, models, _
from odoo.exceptions import UserError, AccessError, ValidationError, Warning

class AccountJournal(models.Model):
    _inherit = "account.journal"

    shared_bank_account = fields.Boolean(string=_("Tài khoản ngân hàng dùng chung tại Chi nhánh"), default=False)
    shared_company_id = fields.Many2one("res.company", string=_("Công ty dùng chung tài khoản"))
    shared_journal_id = fields.Many2one("account.journal", string=_("Sổ nhật ký ngân hàng dùng chung tại Tổng công ty"))

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        company_ids = [do[2] for do in args if do[0] == 'company_id']
        if company_ids:
            if isinstance(company_ids[0], list):
                company_ids = company_ids[0]
            if False in company_ids:
                company_ids.remove(False)
            res = super(AccountJournal, self.with_context(allowed_company_ids=company_ids)).name_search(name, args,
                                                                                                       operator, limit)
        else:
            res = super(AccountJournal, self).name_search(name, args, operator, limit)
        return res
