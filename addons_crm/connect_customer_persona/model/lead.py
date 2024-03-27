from odoo import models


class Booking(models.Model):
    _inherit = "crm.lead"

    def lich_su_tham_kham(self):
        list_val = []
        data = {'name': 'Lịch sử thăm khám'}
        if self.partner_id:
            walkin = self.env['sh.medical.appointment.register.walkin'].sudo().search(
                [('partner_id', '=', self.partner_id.id), ('state', '=', 'Completed')])
            walkin = walkin.filtered(
                lambda w: (w.company_id == self.env.company) or (self.env.company in w.company2_id))
            sorted_walkin = sorted(walkin, key=lambda x: (x['booking_id']['create_date'], x['create_date']))

            for record in sorted_walkin:
                booking = record.booking_id
                service = record.service
                ngay_tu_van = []
                tinh_trang = []
                noi_dung_tu_van = []
                # Xử lý : Ngày tư vấn + tình trạng + nội dung tư vấn
                if booking.consultation_ticket_ids:
                    for line in booking.consultation_ticket_ids:
                        service_consultations = line.consultation_detail_ticket_ids.mapped('service_id')
                        if any(service in service for service in service_consultations):
                            ngay_tu_van.append(line.create_date.strftime('%d-%m-%Y'))
                            tinh_trang.append(
                                line.consultation_detail_ticket_ids.filtered(lambda c: c.service_id in service).mapped(
                                    'health_status'))
                            noi_dung_tu_van.append(
                                line.consultation_detail_ticket_ids.filtered(lambda c: c.service_id in service).mapped(
                                    'schedule'))

                # Xử lý phần BS tư vấn và lễ tân tư vấn
                bsi_tu_van = []
                letan_tu_van = []
                employees = (record.sale_order_id.order_line.mapped('crm_line_id').mapped(
                    'consultants_1') + record.sale_order_id.order_line.mapped('crm_line_id').mapped(
                    'consultants_2')).mapped('employee_ids')

                for employee in employees:
                    name = str(employee.job_id.name)
                    if 'bác sĩ' in name.lower():
                        bsi_tu_van.append(employee.name.title())
                    else:
                        letan_tu_van.append(employee.name.title())

                # Xử lý phần bác sĩ thực hiện
                if record.surgeries_ids and record.surgeries_ids.surgery_team:
                    bac_si_thuc_hien = record.surgeries_ids.surgery_team.filtered(
                        lambda st: "bác sĩ" in str(st.role.name).lower()).mapped('team_member').mapped('name')
                else:
                    bac_si_thuc_hien = record.specialty_ids.specialty_team.filtered(
                        lambda st: "bác sĩ" in str(st.role.name).lower()).mapped('team_member').mapped('name')
                list_val.append({
                    'booking': record.booking_id.name,
                    'ngay_tu_van': ', '.join(ngay_tu_van) if ngay_tu_van else 'Chưa tư vấn',
                    'ngay_thuc_hien': record.service_date_start.strftime(
                        '%d-%m-%Y') if record.service_date_start else 'Chưa thực hiện',
                    'dich_vu': ', '.join(service.mapped('name')),
                    'tinh_trang': ', '.join(tinh_trang) if tinh_trang else '',
                    'noi_dung_tu_van': ', '.join(noi_dung_tu_van) if noi_dung_tu_van else '',
                    'le_tan_tu_van': ', '.join(letan_tu_van),
                    'bsi_tu_van': ', '.join(bsi_tu_van) if bsi_tu_van else '',
                    'bac_si_thuc_hien': ', '.join(bac_si_thuc_hien).title()
                })

                # Kiểm tra xem có tái khám nào gán với PK này không

                evaluations = self.env['sh.medical.evaluation'].sudo().search([('walkin', '=', record.id)],
                                                                             order='create_date asc')
                if evaluations:
                    for evaluation in evaluations:
                        list_val.append({
                            'booking': record.booking_id.name,
                            'ngay_tu_van': '',
                            'ngay_thuc_hien': evaluation.evaluation_start_date.strftime('%d-%m-%Y'),
                            'dich_vu': ', '.join(evaluation.services.mapped('name')),
                            'tinh_trang': evaluation.info_diagnosis or evaluation.notes_complaint,
                            'noi_dung_tu_van': '',
                            'le_tan_tu_van': '',
                            'bsi_tu_van': '',
                            'bac_si_thuc_hien': ', '.join(evaluation.evaluation_team.filtered(lambda et: 'bác sĩ' in str(et.role.name).lower()).mapped('team_member').mapped('name')).title()
                        })

        data.update({'data': list_val})
        return data

    def get_customer_persona(self):
        dict_val = {}
        data = {'name': 'Chân dung khách hàng'}
        if self.partner_id:
            persona = self.partner_id.persona
            list_mong_muon = self.partner_id.desires.filtered(lambda p: p.type == 'desires').mapped('name')
            if list_mong_muon:
                dict_val.update({'mong_muon': list_mong_muon})
            list_noi_lo_lang = self.partner_id.pain_point.filtered(lambda p: p.type == 'pain_point').mapped('name')
            if list_noi_lo_lang:
                dict_val.update({'lo_lang': list_noi_lo_lang})
            list_tinh_cach = persona.filtered(lambda p: p.type == '3').mapped('description')
            if list_tinh_cach:
                dict_val.update({'tinh_cach': list_tinh_cach})
            list_gia_dinh = persona.filtered(lambda p: p.type == '4').mapped('description')
            if list_gia_dinh:
                dict_val.update({'gia_dinh': list_gia_dinh})
            list_tai_chinh = persona.filtered(lambda p: p.type == '5').mapped('description')
            if list_tai_chinh:
                dict_val.update({'tai_chinh': list_tai_chinh})
            list_so_thich = persona.filtered(lambda p: p.type == '6').mapped('description')
            if list_so_thich:
                dict_val.update({'so_thich': list_so_thich})
            list_muc_tieu = persona.filtered(lambda p: p.type == '7').mapped('description')
            if list_muc_tieu:
                dict_val.update({'muc_tieu': list_muc_tieu})
            list_thuong_hieu = persona.filtered(lambda p: p.type == '8').mapped('description')
            if list_thuong_hieu:
                dict_val.update({'thuong_hieu': list_thuong_hieu})
            list_anh_huong = persona.filtered(lambda p: p.type == '9').mapped('description')
            if list_anh_huong:
                dict_val.update({'anh_huong': list_anh_huong})
            list_hanh_vi = persona.filtered(lambda p: p.type == '10').mapped('description')
            if list_hanh_vi:
                dict_val.update({'anh_huong': list_anh_huong})
            list_hoat_dong = persona.filtered(lambda p: p.type == '11').mapped('description')
            if list_hoat_dong:
                dict_val.update({'hoat_dong': list_hoat_dong})
            list_other = persona.filtered(lambda p: p.type == '12').mapped('description')
            if list_other:
                dict_val.update({'other': list_other})
        data.update({'data': dict_val})
        return data

    def view_customer_persona(self):
        domain = self.env['ir.config_parameter'].sudo().get_param('domain_customer_persona_extend')
        url = domain + '/app/customer-portrait/profile?company_id=%s&partner_id=%s' % (
        self.env.company.id, self.partner_id.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
