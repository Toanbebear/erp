# -*- encoding: utf-8 -*-
##############################################################################
#    Copyright (C) 2018 shealth (<http://scigroup.com.vn/>). All Rights Reserved
#    shealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, shealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

from odoo import fields, api, models, _
from odoo.exceptions import UserError

# Operating Theaters (OT) Management
class SHealthCentersOperatingRooms(models.Model):

    OT_STATES = [
        ('Free', 'Free'),
        ('Reserved', 'Reserved'),
        ('Occupied', 'Occupied'),
        ('Not Available', 'Not Available'),
    ]

    ROOM_TYPE = [
        ('Examination', 'Khám bệnh'),
        ('Laboratory', 'Xét nghiệm'),
        ('Imaging', 'Chuẩn đoán hình ảnh'),
        ('MinorSurgery', 'Tiểu phẫu'),
        ('MajorSurgery', 'Đại phẫu'),
        ('Inpatient', 'Lưu bệnh nhân'),
        ('Spa', 'Spa'),
        ('Laser', 'Laser'),
        ('Odontology', 'Nha'),
        ('Pasteurization', 'Thanh trùng - Hộ lý'),
        ('other', 'Khác')
    ]

    _name = 'sh.medical.health.center.ot'
    _description = "Information about the health centers rooms"

    name = fields.Char(string='Room Name', required=True)
    code = fields.Char(string='Room Code', size=32, required=True)
    active = fields.Boolean(default=True)
    room_number = fields.Char(string='Số phòng', size=32)
    # building = fields.Many2one('sh.medical.health.center.building', string='Building')
    institution = fields.Many2one('sh.medical.health.center', string='Health Center', required=True,
                                  default=lambda self: self.env['sh.medical.health.center'].search([('his_company', '=', self.env.companies.ids[0])], limit=1))
    department = fields.Many2one('sh.medical.health.center.ward', string='Khoa/Phòng', required=True)
    related_department = fields.Many2one('sh.medical.health.center.ward', string='Khoa liên quan')
    # location_id = fields.Many2one('stock.location', string='Location')
    info = fields.Text(string='Extra Info')
    state = fields.Selection(OT_STATES, string='Status', default=lambda *a: 'Free')
    is_operating_theater = fields.Boolean('Operating theater')

    room_type = fields.Selection(ROOM_TYPE, string='Loại phòng')

    location_medicine_stock = fields.Many2one('stock.location', 'Stock Medicine', domain="[('usage', '=', 'internal')]")
    location_supply_stock = fields.Many2one('stock.location', 'Stock Supply', domain="[('usage', '=', 'internal')]")

    location_medicine_out_stock = fields.Many2one('stock.location', 'Tủ Thuốc kê đơn về', domain="[('usage', '=', 'internal')]")
    location_supply_out_stock = fields.Many2one('stock.location', 'Tủ Vật tư kê đơn về', domain="[('usage', '=', 'internal')]")

    location_medicine_emer_stock = fields.Many2one('stock.location', 'Tủ Thuốc cấp cứu', domain="[('usage', '=', 'internal')]")
    location_supply_emer_stock = fields.Many2one('stock.location', 'Tủ Vật tư cấp cứu', domain="[('usage', '=', 'internal')]")

    location_sale_stock = fields.Many2one('stock.location', 'Tủ hàng bán', domain="[('usage', '=', 'internal')]")

    non_manage_material = fields.Boolean('Không quản lý VTTH')

    _sql_constraints = [
            ('name_bed_uniq', 'unique (name,institution)', 'The room name is already occupied !')]


    def name_get(self):
        res = []
        for room in self:
            if room.room_number:
                res.append((room.id, _('%s [%s]') % ( room.name[0:50],room.room_number)))
            else:
                res.append((room.id, _('%s') % (room.name[0:50])))
        return res

    @api.onchange('institution')
    def _change_institution(self):
        self.department = False
        # self.code = self.institution.code + '_'

    @api.model
    def create(self, vals):
        # if not (vals.get('location_id')):
        #     department = self.env['sh.medical.health.center.ward'].browse(vals['department'])
        #     stockLocation = self.env['stock.location']
        #     department_location = stockLocation.browse(department.location_id.id)
        #     room_location = stockLocation.create({'name': vals['name'], 'location_id': department_location.id,'company_id':department.institution.company_id.id})
        #     vals['location_id'] = room_location.id

        room = super(SHealthCentersOperatingRooms, self).create(vals)
        return room

    # Preventing deletion of a operating theaters which is not in draft state

    def unlink(self):
        for healthcenter in self.filtered(lambda healthcenter: healthcenter.state in ['Draft','Not Available']):
            raise UserError(_('You can not delete operating theaters(s) which is in "Reserved" or "Occupied" state !!'))
        return super(SHealthCentersOperatingRooms, self).unlink()


    def action_surgery_set_to_not_available(self):
        return self.write({'state': 'Not Available'})


    def action_surgery_set_to_available(self):
        return self.write({'state': 'Free'})


class shealthCentersBeds(models.Model):
    _inherit = 'sh.medical.health.center.beds'

    room = fields.Many2one('sh.medical.health.center.ot', 'Room', domain="[('department', '=', ward)]", ondelete='cascade')


class shealthInpatient(models.Model):
    _inherit = 'sh.medical.inpatient'

    room = fields.Many2one('sh.medical.health.center.ot', 'Phòng', domain="[('department', '=', ward)]", readonly=True,
                           states={'Draft': [('readonly', False)], 'Hospitalized': [('readonly', False)]})

    @api.onchange('ward')
    def _onchange_ward(self):
        self.room = False

    @api.onchange('room')
    def _onchange_room(self):
        self.bed = False

# class shealthCentersBuilding(models.Model):
#
#
#     def _ot_count(self):
#         result = {}
#         oe_ot = self.env['sh.medical.health.center.ot']
#         for building in self:
#             domain = [('building', '=', building.id)]
#             ot_ids = oe_ot.search(domain)
#             ots = oe_ot.browse(ot_ids)
#             ot_count = 0
#             for ot in ots:
#                 ot_count+=1
#             building.ot_count = ot_count
#         return result
#
#     _inherit = 'sh.medical.health.center.building'
#     ot_count = fields.Integer(compute=_ot_count, string="Operation Theaters")
