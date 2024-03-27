from odoo import models


class Walkin(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    def set_index_walkin(self):
        date_list = []
        walkin_dates_list = self.env['sh.medical.appointment.register.walkin'].search([]).mapped('date')
        for date_time in walkin_dates_list:
            date_list.append(date_time.date())
        date_list = sorted(set(date_list))
        for date in date_list:
            walkin_for_date = self.env['sh.medical.appointment.register.walkin'].search(
                [('date', '>=', date.strftime("%Y-%m-%d 00:00:00")),
                 ('date', '<=', date.strftime("%Y-%m-%d 23:59:59"))])
            service_room_list = set(walkin_for_date.mapped('service_room'))
            for service_room in service_room_list:
                walkin_ids = self.env['sh.medical.appointment.register.walkin'].search(
                    [('date', '>=', date.strftime("%Y-%m-%d 00:00:00")),
                     ('date', '<=', date.strftime("%Y-%m-%d 23:59:59")),
                     ('service_room', '=', service_room.id)], order="date asc")
                index_new = 0
                for walkin in walkin_ids:
                    index_new += 1
                    self.env.cr.execute(""" UPDATE sh_medical_appointment_register_walkin
                                            SET index_by_day = %s
                                            WHERE id = %s ;""" % (index_new, walkin.id))
