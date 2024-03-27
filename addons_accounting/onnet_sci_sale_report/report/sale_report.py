from odoo import fields, models

class SaleReport(models.Model):
    _inherit = 'sale.report'

    service_id = fields.Many2one('sh.medical.health.center.service', 'Dịch vụ', readonly=True)
    booking_id = fields.Many2one('crm.lead', 'Mã Booking', readonly=True)
    crm_line_id = fields.Many2one('crm.line', 'Dòng dịch vụ', readonly=True)
    code_customer = fields.Char('Mã khách hàng', readonly=True)
    walkin_id = fields.Many2one('sh.medical.appointment.register.walkin', 'Mã phiếu khám', readonly=True)
    specialty_id = fields.Many2one('sh.medical.specialty', 'Mã phiếu chuyên khoa', readonly=True)
    service_room = fields.Many2one('sh.medical.health.center.ot', 'Phòng thực hiện', readonly=True)
    uom_price = fields.Integer('Đơn vị xử lý', readonly=True)
    surgery_date = fields.Datetime(string='Ngày giờ bắt đầu', help="Start of the Surgery",
                                   default=fields.Datetime.now)
    surgery_end_date = fields.Datetime(string='Ngày giờ kết thúc', help="End of the Surgery")
    services_date = fields.Datetime(string='Ngày thực hiện dịch vụ')
    services_end_date = fields.Datetime(string='Ngày kết thục dịch vụ')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['service_id'] = ", crm.service_id as service_id"
        fields['crm_line_id'] = ", crm.id as crm_line_id"
        fields['booking_id'] = ", s.booking_id as booking_id"
        fields['code_customer'] = ", partner.code_customer as code_customer"
        fields['walkin_id'] = ", walkin.id as walkin_id"
        fields['specialty_id'] = ", ms.id as specialty_id"
        fields['service_room'] = ", walkin.service_room as service_room"
        fields['uom_price'] = ", l.uom_price as uom_price"
        fields['surgery_date'] = ", surgery.surgery_date as surgery_date"
        fields['surgery_end_date'] = ", surgery.surgery_end_date as surgery_end_date"
        fields['services_date'] = ", ms.services_date as services_date"
        fields['services_end_date'] = ", ms.services_end_date as services_end_date"

        groupby += """
            , crm.service_id
            , s.booking_id
            , crm.id
            , partner.code_customer
            , walkin.id
            , ms.id
            , walkin.service_room
            , l.uom_price
            , surgery.surgery_date
            , surgery.surgery_end_date
            , ms.services_date
            , ms.services_end_date
        """
        from_clause += """
            left join crm_line crm on (l.crm_line_id = crm.id)
            left join sh_medical_appointment_register_walkin walkin on (s.id = walkin.sale_order_id)
            left join sh_medical_specialty ms on (walkin.id = ms.walkin)
            left join sh_medical_surgery surgery on (walkin.id = surgery.walkin)
        """
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

