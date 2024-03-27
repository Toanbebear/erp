# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    cr.execute("""
                ALTER TABLE crm_lead DROP amount_paid_ehc;
                """)
