from odoo import fields, models

#
# class MrpWorkorder(models.Model):
#     _inherit = 'mrp.workorder'
#
#     def button_finish(self):
#         result = super(MrpWorkorder, self).button_finish()
#         for workorder in self:
#             for cost_line in workorder.production_id.production_cost_line_ids:
#                 if cost_line.work_center_id == workorder.workcenter_id and cost_line.cost_driver_id.compute_actual_count_base_on_working_hour:
#                     cost_line.actual_count = workorder.duration
#
#         return result