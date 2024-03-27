from odoo import models


class CronApiAccessTokenCs(models.Model):
    _inherit = 'api.access.token.cs'

    def del_api_access_token_cs(self):
        self.env.cr.execute(""" delete from api_access_token_cs WHERE expires <= now();""")
