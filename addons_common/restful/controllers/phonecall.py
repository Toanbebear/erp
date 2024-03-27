"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import logging

from odoo import http
from odoo.addons.restful.common import (
    invalid_response,
    valid_response_once,
)
from odoo.addons.restful.controllers.main import (
    get_url_base,
    validate_token
)
from odoo.http import request

_logger = logging.getLogger(__name__)


class PhoneCallController(http.Controller):

    @validate_token
    @http.route("/api/v1/phone-call", type="http", auth="none", methods=["POST"], csrf=False)
    def create_phone_call(self, **payload):
        ''' API 5.1 Tạo phone call'''
        '''
        payload={
        'type_phonecall': '4',
        'direction': 'out',
        'phone': '123456789',
        'contact_name': 'Đoàn Cao Sơn Z',
        'stage_id': '11',
        'company_id': '2',
        'country_id': '1',
        'state_id': '1',
        'street': 'test',
        'booking_date': '2021-09-09'
        'call_date': '2021-09-09'
        'desc':'ádasd'
        'account_id': '1'
            }
        '''
        values = {}

        # get brand
        brand_id = request.brand_id

        # check các trường require
        field_require = [
            'ticket_id',
            'type_phonecall',
            'direction',
            'phone',
            'contact_name',
            'stage_id',
            'company_id',
        ]
        for field in field_require:
            if field not in payload.keys():
                return invalid_response(
                    "Missing",
                    "The parameter %s is missing!!!" % field)
        try:
            # changing IDs from string to int.
            for k, v in payload.items():
                values[k] = v

            # check partner nếu có account_id
            if 'account_id' in values and len(values['account_id']) != 0:
                partner = request.env['res.partner'].search([('id', '=', values['account_id'])])
                if partner:
                    values['partner_id'] = int(values['account_id'])
                    values.pop('account_id')
                else:
                    return invalid_response("ID Account not found",
                                            "The ID %s not found in system !!!" % int(values['account_id']))
            else:
                partner = request.env['res.partner'].search([('phone', '=', values['phone'])])
                if partner:
                    values['partner_id'] = partner.id
                else:
                    return invalid_response("Phone not found",
                                            "The Phone %s not found in system !!!" % values['phone'])

            # require check company_id & set brand_id
            if 'company_id' in values:
                company = request.env['res.company'].search(
                    [('id', '=', values['company_id']), ('brand_id', '=', brand_id)])
                if company:
                    values['company_id'] = int(values['company_id'])
                    values['brand_id'] = brand_id
                else:
                    return invalid_response("ID Company not found",
                                            "The ID %s not found in system !!!" % int(values['company_id']))

            # check type_phonecall
            type_phone_call = request.env['crm.type'].search([('id', '=', values['type_phonecall'])])
            if type_phone_call:
                values['type_crm_id'] = int(values['type_phonecall'])
                values['name'] = type_phone_call.name + ' ' + values['contact_name']
                values['subject'] = type_phone_call.name
                values.pop('type_phonecall')
            else:
                return invalid_response("ID Type Phone Call not found",
                                        "The ID %s not found in system !!!" % int(values['type_phonecall']))

            # check country_id
            if 'country_id' in values and len(values['country_id']) != 0:
                country = request.env['res.country.state'].browse(values['country_id'])
                if country:
                    values['country_id'] = int(values['country_id'])
                else:
                    return invalid_response("ID Country not found",
                                            "The ID %s not found in system !!!" % int(values['country_id']))

            # check state_id is valid
            if 'state_id' in values and len(values['state_id']) != 0:
                state = request.env['res.country.state'].browse(values['state_id'])
                if state:
                    values['state_id'] = int(values['state_id'])
                else:
                    return invalid_response("ID State not found",
                                            "The ID %s not found in system !!!" % int(values['state_id']))

            # tạo phone call
            _logger.info('=========================== create phone call ==========================================')
            _logger.info(values)
            _logger.info('==================================================================================')
            record_phone_call = request.env['crm.phone.call'].sudo().create(values)
            # ============== trả ouput ===========================
            data = {}
            if record_phone_call:
                phone_call_action_id = request.env.ref('crm_base.action_open_view_phone_call').id
                phone_call_menu_id = request.env.ref('crm_base.crm_menu_phone_call').id
                data['id_phonecall'] = record_phone_call.id
                data[
                    'link_phonecall_detail'] = get_url_base() + "/web#id=%d&model=crm.phone.call&view_type=form&action=%d&menu_id=%d" % (
                    record_phone_call.id,
                    phone_call_action_id, phone_call_menu_id)
            return valid_response_once(data)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("params", e)

    @validate_token
    @http.route("/api/v1/phone-call/<id>", type="http", auth="none", methods=["PUT"], csrf=False)
    def update_phone_call(self, id=None, **payload):
        """ API 5.3 Cập nhật phone call"""
        # get brand
        brand_id = request.brand_id

        # get id
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)

        try:
            values = {}
            # changing IDs from string to int.
            for k, v in payload.items():
                values[k] = v
            # get booking record by id
            record_phone_call = request.env['crm.phone.call'].sudo().search([('id', '=', _id)])
            if record_phone_call:
                # check partner nếu có account_id
                if 'account_id' in values and len(values['account_id']) != 0:
                    partner = request.env['res.partner'].search([('id', '=', values['account_id'])])
                    if partner:
                        values['partner_id'] = int(values['account_id'])
                        values.pop('account_id')
                    else:
                        return invalid_response("ID Account not found",
                                                "The ID %s not found in system !!!" % int(values['account_id']))


                # require check company_id & set brand_id
                if 'company_id' in values and len(values['company_id']) != 0:
                    company = request.env['res.company'].search(
                        [('id', '=', values['company_id']), ('brand_id', '=', brand_id)])
                    if company:
                        values['company_id'] = int(values['company_id'])
                        values['brand_id'] = brand_id
                    else:
                        return invalid_response("ID Company not found",
                                                "The ID %s not found in system !!!" % int(values['company_id']))

                # check country_id
                if 'country_id' in values and len(values['country_id']) != 0:
                    country = request.env['res.country.state'].browse(values['country_id'])
                    if country:
                        values['country_id'] = int(values['country_id'])
                    else:
                        return invalid_response("ID Country not found",
                                                "The ID %s not found in system !!!" % int(values['country_id']))

                # check state_id is valid
                if 'state_id' in values and len(values['state_id']) != 0:
                    state = request.env['res.country.state'].browse(values['state_id'])
                    if state:
                        values['state_id'] = int(values['state_id'])
                    else:
                        return invalid_response("ID State not found",
                                                "The ID %s not found in system !!!" % int(values['state_id']))

                # check type_phonecall
                if 'type_phonecall' in values and len(values['type_phonecall']) != 0:
                    type_phone_call = request.env['crm.type'].search([('id', '=', values['type_phonecall'])])
                    if type_phone_call:
                        values['type_crm_id'] = int(values['type_phonecall'])
                        if 'contact_name' in values and len(values['contact_name']) != 0:
                            values['name'] = type_phone_call.name + ' ' + values['contact_name']
                        else:
                            values['name'] = type_phone_call.name + ' ' + record_phone_call.contact_name
                        values['subject'] = type_phone_call.name
                        values.pop('type_phonecall')
                    else:
                        return invalid_response("ID Type Phone Call not found",
                                                "The ID %s not found in system !!!" % int(values['type_phonecall']))
                # check stage phone call
                if 'stage_id' in values and len(values['stage_id']) != 0:
                    stage = request.env['crm.stage'].search([('id', '=', int(values['stage_id'])), ('rest_api', '=', True)])
                    if stage:
                        values['stage_id'] = int(values['stage_id'])
                    else:
                        return invalid_response("ID Stage not found",
                                                "The ID %s not found in system !!!" % int(values['stage_id']))
                _logger.info('====================================================================================')
                _logger.info(values)
                _logger.info('=====================================================================================')
                # update data
                record_phone_call.write(values)
                data = {}
                if record_phone_call:
                    phone_call_action_id = request.env.ref('crm_base.action_open_view_phone_call').id
                    phone_call_menu_id = request.env.ref('crm_base.crm_menu_phone_call').id
                    data['id_phonecall'] = record_phone_call.id
                    data[
                        'link_phonecall_detail'] = get_url_base() + "/web#id=%d&model=crm.phone.call&view_type=form&action=%d&menu_id=%d" % (
                        record_phone_call.id,
                        phone_call_action_id, phone_call_menu_id)
            else:
                return invalid_response("ID Phone Call not found",
                                        "The ID %s not found in system !!!" % _id)

        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e.name)
        else:
            return valid_response_once(data)
