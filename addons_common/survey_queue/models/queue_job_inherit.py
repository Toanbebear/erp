import json
import logging
from datetime import datetime
from odoo.addons.queue_job.job import job

import requests
from odoo import fields, models, api
from odoo.http import request

_logger = logging.getLogger(__name__)


class CRMCaseInherit(models.Model):
    _inherit = 'queue.job'

    def remove_queue(self, channel):
        list_channel = tuple(channel.split(", "))
        if channel:
            delete = """delete from queue_job
                    where state = 'done' and channel in %s
                    """
            self.env.cr.execute(delete, [tuple(list_channel)])
        else:
            delete = """delete from queue_job
                        where state = 'done'
                        """
            self.env.cr.execute(delete)

