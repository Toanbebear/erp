# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api, exceptions, _
from odoo.addons.queue_job.job import job

class APILog(models.Model):
    _name = 'enterprise.api.log'
    _description = 'Api log'

    name = fields.Char(required=True, translate=True)
    url = fields.Char('url', required=True)
    type = fields.Selection([('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('DELETE', 'DELETE')], default='get', string='Type')
    header = fields.Text(string='Header', required=False)
    request = fields.Text(string='Request', required=False)
    status = fields.Integer(string='Status', size=4)
    response = fields.Text(string='Response', required=True)
    map_id = fields.Many2one('records.com.ent.rel', required=False, ondelete='cascade')

    def _cron_remove_log(self):
        cron = self.env.ref('onnet_sci_api.ir_cron_remove_log')
        domain = []
        if cron:
            interval_number = cron.interval_number
            interval_type = cron.interval_type
            now = datetime.now()
            end = False
            if interval_type == 'days':
                end = now - timedelta(days=interval_number)
            elif interval_type == 'weeks':
                end = now - timedelta(weeks=interval_number)
            elif interval_type == 'months':
                end = now - timedelta(months=interval_number)
            if end:
                domain = [('write_date', '<=', end)]

        records = self.env['enterprise.api.log'].sudo().search(domain, order='id asc')
        if records:
            records.unlink()

class SyncAPI(models.TransientModel):
    _name = 'enterprise.api.sync'
    _description = 'Api Sync'

    model = fields.Selection([('res.country', _('Country')),
                              ('res.country.state', _('State')),
                              ('res.currency', _('Currency')),
                              ('product.category', _('Product category')),
                              ('uom.category', _('UOM Category')),
                              ('uom.uom', _('UOM')),
                              ('product.attribute', _('Product Attribute')),
                              ('product.attribute.value', _('Product Attribute Value')),
                              ('product.template', _('Product Template')),
                              ('product.template.attribute.line', _('Product Attribute Line')),
                              ('res.company', _('Company')),
                              ('product.pricelist', _('Price List')),
                              ('project.project', _('Project')),
                              ('res.partner', _('Partner')),
                              ('res.users', _('User')),
                              ('res.bank', _('Bank')),
                              ('res.partner.bank', _('Partner Bank')),
                              ('res.partner.category', _('Partner Category')),
                              ('account.account', _('account')),
                              ('account.journal', _('Journal')),
                              ('account.move', _('Account Move')),
                              ('account.tax', _('Tax')),
                              ('account.tax.repartition.line', _('Tax Repartition Line')),
                              ('account.payment.term', _('Payment Term')),
                              ('account.analytic.group', _('Analytic Group')),
                              ('account.analytic.account', _('Analytic Account')),
                              ('account.analytic.line', _('Analytic Line'))])


    def action_sync(self):
        self.sudo().with_delay(channel='sync_all').sync_record()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @job
    def sync_record(self):
        self.ensure_one()
        if self.model in ('product.category', 'res.partner'):
            companies = self.env['res.company'].search([])
            for company_id in companies.ids:
                model = self.env[self.model].with_context(allowed_company_ids=[company_id])
                records = model.sudo().search([], order='id asc')
                record_ids = records.ids
                counter = len(record_ids)
                i = 0
                while counter > 0:
                    if counter >= 5000:
                        self.sudo().with_delay(channel='sync_all').sync_batch(model, record_ids[0:4999], company_id)
                        record_ids = record_ids[4999:len(record_ids)]
                    else:
                        self.sudo().with_delay(channel='sync_all').sync_batch(model, record_ids, company_id)
                        record_ids = []
                    i = 1+i
                    counter = len(record_ids)
        else:
            model = self.env[self.model]
            records = model.sudo().search([], order='id asc')
            for record_id in records.ids:
                if self.model == 'res.company':
                    model.sudo().with_delay(channel='sync_all').create_enterprise(record_id)
                else:
                    model.sudo().with_delay(channel='sync_all').sync_record(record_id)

    @job
    def sync_batch(self, model, record_ids, company_id):
        for record_id in record_ids:
            model.with_context(allowed_company_ids=[company_id]).sudo().with_delay(channel='sync_all').sync_record(record_id)
