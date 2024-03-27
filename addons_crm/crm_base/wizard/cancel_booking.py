import datetime

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class CancelBooking(models.TransientModel):
    _name = 'cancel.booking'
    _description = 'Cancel Booking'

    # REASON_OUT_SOLD = [('think_more', 'Suy nghĩ thêm'), ('ask_relationship', 'Hỏi ý kiến người thân'),
    #                    ('not_enough_money', 'Chưa đủ chi phí thực hiện'), ('being_treated', 'Đang điều trị bệnh lý'),
    #                    ('not_enough_consult', 'Bác sĩ tư vấn chưa đủ thời gian để làm DV'),
    #                    ('consult_not_improve', 'Bác sĩ tư vấn không cải thiện'),
    #                    ('treated_another_company', 'Khách đang điều trị tại cơ sở khác'),
    #                    ('1', 'KH đến tham khảo chưa có ý định làm'),
    #                    ('2', 'KH trên 60 tuổi'),
    #                    ('3', 'KH chờ người nhà,tái khám,thay băng,cắt chỉ nên tư vấn tham khảo'),
    #                    ('4', 'KH không đủ thời gian ở Việt Nam'),
    #                    ('5', 'Nhu cầu của KH quá cao,bệnh viện chưa đáp ứng được'),
    #                    ('6', 'KH dưới 18 tuổi'),
    #                    ('7', 'KH dùng 2 sđt,mỗi lần tư vấn đăng ký 1 số khác nhau'),
    #                    ('8', 'Chi phí chênh lệch giữa báo giá qua tổng đài và thực tế'),
    #                    ('9', 'KH đến tư vấn trực tiếp nhưng vội về,báo giá qua điện thoại'),
    #                    ('10', 'KH tham gia hội thảo để lấy quà, chưa có nhu cầu làm'),
    #                    ('11', 'Khách cắt chỉ,tái khám,thay băng,tư vấn tham khảo thêm'),
    #                    ('12', 'Không cải thiện'),
    #                    ]
    REASON_OUT_SOLD = [('ask_relationship', 'Hỏi ý kiến người thân'), ('being_treated', 'Sức khỏe chưa đảm bảo'),
                       ('not_enough_consult', 'Không đủ thời gian thực hiện dịch vụ'),
                       ('treated_another_company', 'Đang điều trị tại cơ sở khác'),
                       ('1', 'Tư vấn tham khảo chưa có nhu cầu'),
                       ('5', 'Nhu cầu khách hàng quá cao cơ sở không đáp ứng được'),
                       ('7', 'Trùng Booking cũ'),
                       ('8', 'Chất lượng tư vấn (Không đồng nhất (Chuyên môn/chi phí), thái độ tư vấn...)'),
                       ('10', 'Chỉ có nhu cầu nhận quà tặng'), ('13', 'Chi phí cao hơn các đơn vị khác'),
                       ('14', 'Không đủ chi phí'),
                       ('15', 'Phát sinh chi phí với dự tính ban đầu'), ('16', 'Chưa sắp xếp được thời gian'),
                       ('17', 'Chưa tin tưởng về chất lượng (Chuyên môn, cơ sở...)'),
                       ('18', 'Gặp vấn đề tâm lý (Sợ đau/lo lắng...)'), ('19', 'Người thân không cho làm'),
                       ('20', 'Tham khảo thêm cơ sở khác'),
                       ('21', 'Chống chỉ định bác sĩ'), ('22', 'Khách hàng mang thai'), ('23', 'Độ tuổi không phù hợp')]
    REASON_CANCEL_BOOKING = [('cus_cancel_booking_date', 'Khách hàng hủy lịch'),
                             ('cus_are_being_treated', 'Khách đang điều trị bệnh lý'),
                             ('wrong_appointment', 'Thao tác sai lịch hẹn'), ('other', 'Lý do khác (Ghi rõ nội dung)')]
    name = fields.Text('Reason')
    type_action = fields.Selection([('cancel', 'Hủy Booking'), ('out_sold', 'Out sold')], string='Thao tác thực hiện')
    booking_id = fields.Many2one('crm.lead', string='Booking')
    customer_come = fields.Selection(related='booking_id.customer_come')
    reason_cancel_booking = fields.Selection(REASON_CANCEL_BOOKING, string='Lý do hủy')
    reason_out_sold = fields.Selection(REASON_OUT_SOLD, string='Lý do out sold')
    REASON_LINE_CANCEL = [('change_service', 'Đổi sang dịch vụ khác cùng nhóm'),
                          ('due_to_illness', 'Hủy do bệnh lý'), ('create_wrong_service', 'Thao tác tạo sai dịch vụ'),
                          ('not_money', 'Không đủ chi phí'), ('consultant', 'Tham khảo trước'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy dịch vụ')

    def set_cancel(self):
        for rec in self:
            if rec.booking_id:
                if rec.booking_id.stage_id in [self.env.ref('crm_base.crm_stage_cancel'),
                                               self.env.ref('crm_base.crm_stage_out_sold')]:
                    raise ValidationError(
                        'Booking này hiện đang ở trạng thái %s' % rec.booking_id.stage_id.name.upper())
                # if rec.customer_come == 'yes':
                #     payment = self.env['account.payment'].sudo().search([('crm_id', '=', self.booking_id.id)])
                #     if not payment:
                #         raise ValidationError('Khách hàng đến cửa nhưng không chốt được dịch vụ => Bạn cần thực hiện OUT SOLD BOOKING')
                # for line in rec.booking_id.crm_line_ids:
                #     if line.stage in ['processing', 'done', 'waiting']:
                #         raise ValidationError('Bạn không thể hủy Booking này!!!')

                if rec.customer_come == 'yes':
                    raise ValidationError(
                        'Khách hàng đến cửa nhưng không chốt được dịch vụ => Bạn cần thực hiện OUT SOLD BOOKING')
                rec.booking_id.stage_id = self.env.ref('crm_base.crm_stage_cancel').id
                rec.booking_id.reason_cancel_booking = rec.reason_cancel_booking
                rec.booking_id.special_note = rec.name
                rec.booking_id.effect = 'expire'
                rec.booking_id.crm_line_ids.write({
                    'stage': 'cancel',
                    'reason_line_cancel': self.reason_line_cancel,
                    'note': self.name if self.name else 'Booking hủy',
                    'status_cus_come': 'no_come',
                    'cancel_user': self.env.user,
                    'cancel_date': datetime.datetime.now()
                })
                for line in rec.booking_id.statement_service_ids:
                    line.sudo().unlink()
                # hủy phonecall chưa xác nhận
                pc = self.env['crm.phone.call'].search([('crm_id', '=', rec.booking_id.id), ('state', '=', 'draft')])
                for item in pc:
                    item.state = 'cancelled'

    def set_out_sold(self):
        for rec in self:
            if rec.booking_id:
                if rec.booking_id.stage_id in [self.env.ref('crm_base.crm_stage_cancel'),
                                               self.env.ref('crm_base.crm_stage_out_sold')]:
                    raise ValidationError(
                        'Booking này hiện đang ở trạng thái %s' % rec.booking_id.stage_id.name.upper())
                if rec.customer_come == 'no':
                    raise ValidationError(
                        'Khách hàng chưa đến và không muốn làm dịch vụ nữa => Bạn cần thực hiện HỦY/CANCEL BOOKING')
                for line in rec.booking_id.crm_line_ids:
                    if (line.company_id.brand_id == self.env.ref('sci_brand.res_brand_paris')) and (
                    not line.crm_information_ids):
                        raise ValidationError('DỊCH VỤ %s THIẾU THÔNG TIN TƯ VẤN VIÊN' % line.product_id.name)
                    if line.stage in ['processing', 'done', 'waiting']:
                        raise ValidationError('Bạn không thể Out sold Booking này!!!')
                rec.booking_id.stage_id = self.env.ref('crm_base.crm_stage_out_sold').id
                rec.booking_id.reason_out_sold = rec.reason_out_sold
                rec.booking_id.date_out_sold = fields.Date.today()
                rec.booking_id.effect = 'expire'
                rec.booking_id.crm_line_ids.write({
                    'stage': 'cancel',
                    'note': 'Booking out sold',
                    'status_cus_come': 'come_no_service'
                })
                for line in rec.booking_id.statement_service_ids:
                    line.sudo().unlink()


class CancelCRMLine(models.TransientModel):
    _name = 'crm.line.cancel'
    _description = 'Cancel CRM Line'

    crm_line_id = fields.Many2one('crm.line', string='Dịch vụ')
    REASON_LINE_CANCEL = [('change_service', 'Đổi sang dịch vụ khác cùng nhóm'),
                          ('due_to_illness', 'Hủy do bệnh lý'), ('create_wrong_service', 'Thao tác tạo sai dịch vụ'),
                          ('not_money', 'Không đủ chi phí'), ('consultant', 'Tham khảo trước'),
                          ('other', 'Lý do khác (Ghi rõ lý do)')]
    reason_line_cancel = fields.Selection(REASON_LINE_CANCEL, string='Lý do hủy dịch vụ')
    name = fields.Char('Ghi chú')

    def cancel_crm_line(self):
        self.crm_line_id.stage = 'cancel'
        self.crm_line_id.gia_truoc_huy = self.crm_line_id.total
        self.crm_line_id.reverse_prg_ids()
        self.crm_line_id.reason_line_cancel = self.reason_line_cancel
        self.crm_line_id.note = self.name
        self.crm_line_id.cancel = True
        self.crm_line_id.cancel_user = self.env.user
        self.crm_line_id.cancel_date = datetime.datetime.now()
