# -*- coding: utf-8 -*-
from odoo import fields, models, api


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('xls', "Excel")])
    
    @api.model
    def add_field_arch(self,values):
        view = self.search([('id','=',int(values.get('view_id')))])
        fields_arch = ""
        for field in values.get('fields'):
            fields_arch += "<field name='%s' />\n"%field
        old_arch = view.arch_db.split('<xls>')[1].split('</xls>')[0]
        view.arch_db = """<?xml version="1.0"?>
                <xls>
                 %s
                 %s
                </xls>"""%(old_arch,fields_arch)
