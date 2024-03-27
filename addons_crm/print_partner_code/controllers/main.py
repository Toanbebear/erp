import json
import json
import logging

from odoo.addons.restful.controllers.main import (
    get_url_base,
)

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

gender = {
    'male': 'Nam',
    'female': 'Nữ',
    'other': 'Khác'
}

gender_r = {
    'Nam': 'male',
    'Nữ': 'female',
    'Khác': 'other'
}


def get_gender(value):
    if value:
        return gender[value]
    else:
        return ''


class CheckinController(http.Controller):

    @http.route("/datatable/get-data-qr", type="http", methods=["POST"], csrf=False)
    def get_data_checkin(self, **payload):
        if 'query' in payload:
            input = set(payload.get('query').split(','))
            if len(input) < 15:
                request.env.cr.execute(''' select code from print_partner_code_data where printed = False ''')
                data_check = request._cr.fetchall()
                list_check = []
                for dc in data_check:
                    list_check.append(dc[0])
                if len(list_check) < 15:
                    len_check = 15 - len(list_check)
                    data_create = []
                    int_check = 0
                    for p in input:
                        int_check += 1
                        if int_check != len_check and p:
                            booking = request.env['crm.lead'].sudo().search(
                                [('name', '=', p.strip()), ('type', '=', 'opportunity')], limit=1)
                            if booking and booking.partner_id.code_customer and booking.partner_id.code_customer not in list_check:
                                data_create.append({
                                    'code': booking.partner_id.code_customer,
                                    'name': booking.partner_id.name,
                                    'gender': get_gender(booking.gender),
                                    'birth_date': booking.partner_id.birth_date.strftime(
                                        '%d/%m/%Y') if booking.partner_id.birth_date else '',
                                    'company_id': request.env.company.id,
                                    'partner_id': booking.partner_id.id,
                                })
                                continue
                            partner = request.env['res.partner'].sudo().search(
                                ['|', ('phone', '=', p.strip()), ('code_customer', '=', p.strip())], limit=1)
                            if partner and partner.code_customer not in list_check:
                                data_create.append({
                                    'code': partner.code_customer,
                                    'name': partner.name,
                                    'gender': get_gender(partner.gender),
                                    'birth_date': partner.birth_date.strftime('%d/%m/%Y') if partner.birth_date else '',
                                    'company_id': request.env.company.id,
                                    'partner_id': partner.id,
                                })
                                continue
                datas = request.env['print.partner.code.data'].sudo().create(data_create)
                data_render = request.env['print.partner.code.data'].sudo().search(
                    [('company_id', '=', request.env.company.id), ('printed', '!=', True)])
                data = []
                data_id = []
                stt = 0

                partner_action_id = request.env.ref('contacts.action_contacts').id
                partner_menu_id = request.env.ref('contacts.menu_contacts').id
                for d in data_render:
                    stt += 1
                    data_id.append(d.id)
                    acc_url = get_url_base() + "/web#id=%d&action=%d&model=res.partner&view_type=form&menu_id=%d" % (
                        d.partner_id.id, partner_action_id, partner_menu_id)
                    data.append([
                        stt,
                        d.code,
                        d.name,
                        d.gender,
                        d.birth_date,
                        "<a href='%s' target='new'> Mở</a>" % (
                            acc_url) + ' | ' + "<button style='border:none;background: none;color:#063d7d' type='button' class='b' data-id='%s''>Xóa</button>" % d.id
                    ])
                return json.dumps({
                    'iTotalRecords': len(data),
                    'iTotalDisplayRecords': len(data),
                    'data': data,
                    'success': 0,
                })
            else:
                return json.dumps({
                    'iTotalRecords': 0,
                    'iTotalDisplayRecords': 0,
                    'data': [],
                    'success': 1,
                })
        else:
            data_render = request.env['print.partner.code.data'].sudo().search(
                [('company_id', '=', request.env.company.id), ('printed', '!=', True)])
            data = []
            data_id = []
            stt = 0
            partner_action_id = request.env.ref('contacts.action_contacts').id
            partner_menu_id = request.env.ref('contacts.menu_contacts').id
            for d in data_render:
                stt += 1
                data_id.append(d.id)
                acc_url = get_url_base() + "/web#id=%d&action=%d&model=res.partner&view_type=form&menu_id=%d" % (
                    d.partner_id.id, partner_action_id, partner_menu_id)
                data.append([
                    stt,
                    d.code,
                    d.name,
                    d.gender,
                    d.birth_date,
                    "<a href='%s' target='new'> Mở</a>" % (
                        acc_url) + ' | ' + "<button style='border:none;background: none;color:#063d7d' type='button' class='b' data-id='%s''>Xóa</button>" % d.id
                ])
            return json.dumps({
                'iTotalRecords': len(data),
                'iTotalDisplayRecords': len(data),
                'data': data,
                'success': 0,
            })

    @http.route("/datatable/clear-data-qr", type="http", methods=["POST"], csrf=False)
    def clear_data_checkin(self, **payload):
        request.env.cr.execute(''' delete from print_partner_code_data ''')
        return json.dumps({
            'iTotalRecords': 0,
            'iTotalDisplayRecords': 0,
            'data': [],
            'success': 0,
        })

    @http.route("/datatable/delete-record-qr", type="json", methods=["POST"], csrf=False)
    def delete_record_qr(self, **payload):
        if payload.get('id'):
            request.env.cr.execute(
                ''' delete from print_partner_code_data ppcd where ppcd.id = %s ''' % int(payload.get('id')))
        return json.dumps({
            'cc' : 'll'
        })
