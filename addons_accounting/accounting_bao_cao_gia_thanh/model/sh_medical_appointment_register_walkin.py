from odoo import fields, models, SUPERUSER_ID
from datetime import date, datetime, timedelta, time
from odoo.addons.queue_job.job import ENQUEUED, Job
from odoo.addons.queue_job.controllers.main import RunJobController
import logging
_logger = logging.getLogger(__name__)

class AppoinmentRegisterWalkin(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    def compute_cost_line(self):
        for walkin in self:
            # step 2.1: phieu xet nghiem
            for lab_test in walkin.lab_test_ids:
                if lab_test.state.lower() == 'completed':
                    lab_test.auto_compute_cost_line()

            # step 2.2: phieu phau thuat thu thuat
            for surgery in walkin.surgeries_ids:
                if surgery.state.lower() == 'done':
                    surgery.auto_compute_cost_line()

            # step 2.3: phieu chuyen khoa
            for specialty in walkin.specialty_ids:
                if specialty.state.lower() == 'done':
                    specialty.auto_compute_cost_line()

            # step 2.4: benh nhan luu
            patient = walkin.inpatient_ids
            for patient_rounding in patient.roundings:
                if patient_rounding.state.lower() == 'done':
                    patient_rounding.auto_compute_cost_line()

            # step 2.5: don thuoc
            for prescription in walkin.prescription_ids:
                if prescription.state == 'Đã xuất thuốc':
                    prescription.auto_compute_cost_line()


    def _auto_compute_cost_line(self, start = False, end = False, walkin_ids=False):
        # step 1: tim phieu kham da hoan thanh 2 ngay truoc
        if not start:
            start = (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=-2))
        else:
            start = datetime.strptime(start, '%Y-%m-%d').date()

        if not end:
            end = (datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=-1))
        else:
            end = datetime.strptime(end, '%Y-%m-%d').date()

        if not walkin_ids:
            walkins = self.sudo().search([
                ('state', '=', 'Completed'),
                ('close_walkin', '>=', start),
                ('close_walkin', '<', end)
            ])
        else:
            walkins = self.sudo().search([
                ('id', 'in', walkin_ids)
            ])

        # step 2: tinh toan cost line tung phieu
        if walkins:
            walkins.compute_cost_line()

    # Disable auto compute costline after compute walkin
    # If you want to enable it again, please uncomment it
    def set_to_completed(self):
        res = super(AppoinmentRegisterWalkin, self).set_to_completed()
        for record in self:
            # 5 minutes after complete walkin, job will execute.
            record.sudo().with_delay(eta=60 * 5).queue_compute_cost_line(record.id, record.company_id, self.env.user.id)
        return res

    def queue_compute_cost_line(self, walkin_id, sci_company_id, sci_user_id):
        walkin = self.env['sh.medical.appointment.register.walkin']. browse(walkin_id)
        if walkin.exists():
            walkin.with_context(allowed_company_ids=[sci_company_id.id]).with_user(sci_user_id).sudo().compute_cost_line()

    def _auto_compute_cost_line_pending_job(self, from_time=20, to_time=7, number_of_record=50):
        try:
            now = fields.Datetime.now()
            now_time = now.time()
            if now_time >= time(from_time, 00) or now_time <= time(to_time, 00):
                fail_jobs = self.env['queue.job'].sudo().search([('state', 'in', ['failed', 'started']), ('func_string', 'like', 'queue_compute_cost_line')], limit=number_of_record)
                env = self.env(user=SUPERUSER_ID)
                for fail_job in fail_jobs:
                    print(fail_job)
                    job = Job.load(env, fail_job.uuid)
                    RunJobController._try_perform_job(self, env, job)
        except Exception as err:
            _logger.debug("%s Exception, queue job", str(err))
