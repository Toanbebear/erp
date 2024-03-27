from lxml import etree
from odoo import api,models

class Hide_Button(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):
        res = super(Hide_Button, self).fields_view_get(view_id=view_id, view_type=view_type,toolbar=toolbar, submenu=False)
        group_id = self.env.user.has_group('permit_export_module.group_permit_export_button')
        doc = etree.XML(res['arch'])
        if not group_id:
            if view_type == 'tree':
                nodes = doc.xpath("//tree")
                for node in nodes:
                    node.set('export_xlsx', '0')
                res['arch'] = etree.tostring(doc)
        return res
