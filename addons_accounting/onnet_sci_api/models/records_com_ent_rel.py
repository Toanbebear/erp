# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.addons.queue_job.job import job

class RecordsComEntRel(models.Model):
    _name = 'records.com.ent.rel'
    _description = 'Records map'

    model = fields.Char(string=_('Model'))
    com_id = fields.Integer(string=_('Community record Id'))
    ent_id = fields.Integer(string=_('Enterprise record Id'))
    action = fields.Selection([('update', _('Update')), ('delete', 'Delete')], string=_('Action'), default='update')
    status = fields.Selection([('failed', _('Failed')), ('success', _('Success'))], string=_('Status'),
                              default='success')
    active = fields.Boolean(string=_('Active'), default=True)
    name = fields.Char(string=_('Name'), compute='_compute_name')
    log_ids = fields.One2many(
        'enterprise.api.log', 'map_id', 'Logs')

    @api.depends('com_id', 'model')
    def _compute_name(self):
        for rec in self:
            rec.name = ''
            if rec.model and rec.com_id:
                record = self.env[rec.model].sudo().browse(rec.com_id)
                if hasattr(record, 'name') and record.name:
                    rec.name = record.name

    @job
    def sync_to_enterprise(self):
        for rec in self:
            self.sudo().with_delay().sync(rec)

    @job
    def sync(self, rec):
        if not rec.model == 'account.move.line':
            self.env[rec.model].sync_record(rec.com_id)
