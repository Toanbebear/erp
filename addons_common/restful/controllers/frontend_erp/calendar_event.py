"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import json
import logging
import ast
from datetime import timedelta, datetime, date
from odoo import http
from odoo.addons.restful.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.addons.restful.controllers.main import (
    validate_token
)
from odoo.http import request

_logger = logging.getLogger(__name__)


class CalendarEventController(http.Controller):
    @http.route("/api/v1/fe/calendar-event", type="http", auth="none", methods=["GET"], csrf=False)
    def get_calendar(self, **payload):
        try:
            domain = ""
            if 'company_id' in payload:
                company = json.loads(payload.get('company_id'))
                if len(company) > 1:
                    domain += " and ce.company_id in %s" % str(tuple(company))
                else:
                    domain += " and ce.company_id = %s" % str(company[0])
            if 'date' in payload:
                if payload.get('date') == 'now':
                    domain += " and ce.start_datetime >= '%s' and ce.start_datetime <= '%s' " % (
                        str(datetime.now().replace(hour=0, minute=0, second=0)), str(datetime.now()))
                elif payload.get('date') == 'last7day':
                    domain += " and ce.start_datetime >= '%s' and ce.start_datetime <= '%s' " % (
                        str((datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0)),
                        str(datetime.now() - timedelta(hours=7)))
                elif payload.get('date') == 'last30day':
                    domain += " and ce.start_datetime >= '%s' and ce.start_datetime <= '%s' " % (
                        str((datetime.now() - timedelta(days=30)).replace(hour=0, minute=0, second=0)),
                        str(datetime.now() - timedelta(hours=30)))
                elif payload.get('date') == 'during':
                    if 'start_date' in payload and 'end_date' in payload:
                        start_date = datetime.strptime(payload['start_date'], '%Y-%m-%d').replace(hour=0, minute=0,
                                                                                                  second=0)
                        end_date = datetime.strptime(payload['end_date'], '%Y-%m-%d').replace(hour=23, minute=59,
                                                                                              second=59)
                        domain += " and ce.start_datetime >= '%s' and ce.start_datetime <= '%s' " % (
                            str(start_date),
                            str(end_date))
            if 'name' in payload:
                domain += """
                    and (ce."name" ilike '%{0}%'
                    or cl."name" ilike '%{0}%'
                    or he."name" ilike '%{0}%'
                    or rc."name" ilike '%{0}%'
                    or rp."name" ilike '%{0}%'
                    )
                """.format(payload['name'])
            query = """
                    SELECT count(ce.id)
                      from calendar_event ce 
                    
                    left join crm_lead cl on ce.opportunity_id = cl.id 
                    left join res_partner rp on ce.customer_id = rp.id 
                    left join sh_medical_physician smp on ce.physician = smp.id 
                    left join hr_employee he on smp.employee_id = he.id
                    left join res_company rc on ce.company_id = rc.id
                    
                    WHERE ce.active = True
                    %s
                """ % domain


            request.cr.execute(query)
            count = request.env.cr.fetchone()[0] or 0
            data = []

            #
            #
            #
            #
            #
            #
            #
            query = """
                    select 
                            ce.id,
                            ce."name",
                            ce.opportunity_id,
                            ce.customer_id,
                            ce.physician,
                            ce.company_id,
                            ce.start_datetime,
                            cl."name" ,
                            rp."name",
                            he."name",
                            rc."name"
                    from calendar_event ce 
                    
                    left join crm_lead cl on ce.opportunity_id = cl.id 
                    left join res_partner rp on ce.customer_id = rp.id 
                    left join sh_medical_physician smp on ce.physician = smp.id 
                    left join hr_employee he on smp.employee_id = he.id
                    left join res_company rc on ce.company_id = rc.id
                    
                    WHERE ce.active = True
                    %s
                    order by ce.id desc
                    offset %s
                    limit %s
                    
                """ % (domain, payload.get('offset'), payload.get('length'))

            request.cr.execute(query)
            datas = request.env.cr.fetchall()
            for rec in datas:
                data.append([
                    rec[0],
                    rec[1] if rec[1] else '',
                    rec[7] if rec[7] else '',
                    rec[8] if rec[8] else '',
                    rec[9] if rec[9] else '',
                    rec[10] if rec[10] else '',
                    str(rec[6] + timedelta(hours=7)) if rec[6] else '',
                ])
            return json.dumps({
                'error': 0,
                'data': {
                    'iTotalRecords': count,
                    'iTotalDisplayRecords': count,
                    'data': data
                }
            })
        except:
            return json.dumps({
                'error': 1,
                'data': {
                    'iTotalRecords': 0,
                    'iTotalDisplayRecords': 0,
                    'data': []
                }
            })
