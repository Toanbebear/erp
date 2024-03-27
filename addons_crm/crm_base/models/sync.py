import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CrmSync(models.Model):
    _name = 'crm.sync'
    _description = 'Crm Sync'

    name = fields.Char('Name')
    ip = fields.Char('IP')
    port = fields.Char('Port')
    database = fields.Char('Database')
    user = fields.Char('User')
    brand_id = fields.Many2many('res.brand', string='Brand sync')
    password = fields.Char('Password')
    history_id = fields.One2many('crm.record.history', 'crm_sync_id', string='History')
    domain = fields.Char(string="Domain", default="[]")
    start_time_sync = fields.Datetime('The date the data was retrieved')
    stage_sync = fields.Many2many('crm.stage', string='Stage sync')
    limit = fields.Integer('Limit')

    def check_user(self, login, name):
        user = self.env['res.users'].search([('login', '=', login)])
        if user:
            return user
        else:
            user = self.env['res.users'].sudo().create({
                'name': name,
                'login': login,
                'email': login,
            })
            return user

    def search_source(self, lead):
        # TH1: nguồn là insight và có source mkt thì nguồn đồng bộ sẽ là nguồn có gắn tag source
        # TH2: nguồn là insight và ko có source mkt thì nguồn đồng bộ
        # sẽ là nguồn đc tìm thấy dựa trên dữ liệu ở trường content

        if lead.source_id.id == 6:
            if lead.source_mkt:
                tag = self.env['crm.tag.source'].search([('code', '=', lead.source_mkt.id)])
                source = self.env['utm.source'].search([('tag_ids', 'in', tag.id)], limit=1)
            else:
                source = self.env['utm.source'].search([('name', '=', lead.source_id.content)])
            return source
        else:
            source = self.env['utm.source'].search([('name', '=', lead.source_id.content)])
            return source

    def create_lead(self, lead):
        brand = self.env['res.brand'].search([('id_brand_insight', '=', lead.brand_sci.id)], limit=1)
        if lead.stage_id.id == self.env.ref('crm_base.crm_stage_bk_insight').crm_stage_insight_id:
            stage = self.env.ref('crm_base.crm_stage_bk_insight')
        else:
            stage = self.env['crm.stage'].search([('crm_stage_insight_id', '=', lead.stage_id.id)], limit=1)
        user = self.check_user(lead.write_uid.login, lead.write_uid.name)
        source = self.search_source(lead)
        lead = self.env['crm.lead'].create({
            'name': lead.contact_name if lead.contact_name else 'Không tên',
            'contact_name': lead.contact_name if lead.contact_name else 'Không tên',
            'phone': lead.phone.replace(" ", ""),
            'mobile': lead.mobile,
            'type': 'lead',
            'stage_id': stage.id,
            'lead_insight': True,
            'brand_id': brand.id,
            'create_by': user.id,
            'user_id': user.id,
            'create_on': lead.create_date,
            'source_id': source.id,
            'category_source_id': source.category_id.id,
            'type_data': 'old' if self.env['crm.lead'].search([('phone', '=', lead.phone)]) else 'new',
            'description': lead.desc,
            'gclid': lead.referred,
        })
        return lead

    def sync(self):
        _logger.info("Sync ..... ")
        # sync = self.env.ref('crm_base.sync_insight')
        # odoo = odoorpc.ODOO(host=sync.ip, port=sync.port)
        # odoo.login(sync.database, sync.user, sync.password)
        # model_sync = odoo.env['crm.lead']
        # ids = sync.history_id.mapped('record_sync')
        # list_brand = sync.brand_id.mapped('id_brand_insight')
        # list_stage = sync.stage_sync.mapped('crm_stage_insight_id')
        # domain = literal_eval(sync.domain) + [('id', 'not in', ids), ('phone', '!=', False)] + \
        #          [('create_date_sci', '>=', sync.start_time_sync.strftime("%m-%d-%Y %H:%M:%S"))] + \
        #          [('brand_sci', 'in', list_brand)] + \
        #          [('stage_id', 'in', list_stage)]
        # record_ids = model_sync.search(domain, limit=sync.limit)
        # records = model_sync.browse(record_ids)
        # for ld in records:
        #     _logger.warning(ld)
        #     lead = self.create_lead(ld)
        #     his = self.env['crm.record.history'].create({
        #         'crm_sync_id': sync.id,
        #         'record_sync': ld.id,
        #         'current_record': lead.id,
        #     })


class RecordHistory(models.Model):
    _name = 'crm.record.history'
    _description = 'Record History'
    _rec_name = 'crm_sync_id'

    name = fields.Char('Name')
    crm_sync_id = fields.Many2one('crm.sync', string='Crm sync')
    record_sync = fields.Char('Record sync')
    current_record = fields.Char('Current record')
