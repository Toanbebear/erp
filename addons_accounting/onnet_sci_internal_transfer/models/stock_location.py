from odoo import models, fields, api, exceptions, _
from odoo.osv import expression

class StockLocation(models.Model):
    _inherit = 'stock.location'

    def search(self, args, **kwargs):
        res = super(StockLocation, self).search(args, **kwargs)
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        # if self.env.context.get('with_sudo'):
        #     return super(StockLocation, self.sudo()).name_search(name, args, operator)
        if isinstance(args, list):
            company_ids = [do[2] for do in args if do[0] == 'company_id']
            domain_company_default = self.env.context.get('domain_company_default', False)
            if domain_company_default and domain_company_default not in company_ids:
                company_ids.append(domain_company_default)
                args = expression.OR([args, [('company_id', '=', domain_company_default)]])
            if company_ids:
                if isinstance(company_ids[0], list):
                    company_ids = company_ids[0]
                if False in company_ids:
                    company_ids.remove(False)
                return super(StockLocation, self.with_context(allowed_company_ids=company_ids).sudo()).name_search(name, args, operator, limit)
        return super(StockLocation, self).name_search(name, args, operator, limit)