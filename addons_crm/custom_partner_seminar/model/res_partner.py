from odoo import models, fields, api

seminar_customers = [
	('normal', 'KH bình thường'),
	('seminar', 'KH hội thảo')
]


class ResPartnerCustom(models.Model):
	_inherit = 'res.partner'
	_description = 'Res Partner Seminar'

	seminar_customers = fields.Selection(seminar_customers, string='KH Hội thảo')