from odoo import fields, models


class UserSync(models.Model):
    _name = 'user.sync'
    _description = 'User sync'

    name = fields.Char('Name')
    ip = fields.Char('IP')
    port = fields.Char('Port')
    database = fields.Char('Database')
    user = fields.Char('User')
    password = fields.Char('Password')
    history_id = fields.One2many('user.record.history', 'user_sync_id', string='History')
    domain = fields.Char(string="Domain", default="[]")
    start_time_sync = fields.Datetime('Ngày dữ liệu được truy xuất')
    limit = fields.Integer('Limit', default=100)

    def create_user(self, us):
        user = self.env['res.users'].sudo().create({'name': us.name,
                                                    'image_1920': us.image_1920,
                                                    'login': us.login,
                                                    'groups_id': [(6, 0, us.groups_id.ids)],
                                                    'company_id': us.company_id.id,
                                                    'company_ids': [(6, 0, us.company_ids.ids)],
                                                    'email': us.work_email})
        return user

    def sync(self):
        sync = self.env.ref('sci_hrms.sync_user')
        # odoo = odoorpc.ODOO(host=sync.ip, port=sync.port)
        # odoo.login(sync.database, sync.user, sync.password)
        # model_sync = odoo.env['res.users']
        # ids = sync.history_id.mapped('record_sync')
        # domain = literal_eval(sync.domain) + [('id', 'not in', ids)]
        # record_ids = model_sync.search(domain, limit=sync.limit)
        # records = model_sync.browse(record_ids)
        # DataUser = self.env['res.users'].sudo()
        # for ld in records:
        #     userinfo = DataUser.search([('login', '=', ld.login)], limit=1)
        #     if not userinfo:
        #         userNew = self.create_user(ld)
        #         userid = userNew.id
        #         username = userNew.name
        #     else:
        #         userid = userinfo.id
        #         username = userinfo.name
        #
        #     self.env['user.record.history'].create({
        #         'user_sync_id': sync.id,
        #         'record_sync': ld.id,
        #         'record_sync_name': ld.name,
        #         'current_record': userid,
        #         'current_record_name': username,
        #     })


class RecordHistory(models.Model):
    _name = 'user.record.history'
    _description = 'User record history'

    name = fields.Char('Name')
    user_sync_id = fields.Many2one('user.sync', string='user sync')
    record_sync = fields.Char('Record sync')
    record_sync_name = fields.Char('Record sync')
    current_record = fields.Char('Current record')
    current_record_name = fields.Char('Current record')
