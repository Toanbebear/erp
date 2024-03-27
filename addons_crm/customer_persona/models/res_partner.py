from odoo import models, fields, api


class CustomPersona(models.Model):
    _inherit = 'res.partner'
    _description = 'Customer Persona'

    marital_status = fields.Selection(
        [('single', 'Độc thân'), ('in_love', 'Đang yêu'), ('engaged', 'Đính hôn'), ('married', 'Đã kết hôn'),
         ('divorce', 'Ly hôn'), ('other', 'Khác')], string='Tình trạng hôn nhân', tracking=True)
    acc_facebook = fields.Char('Facebook Account', tracking=True)
    acc_zalo = fields.Char('Zalo Account', tracking=True)
    hobby = fields.Many2many('hobbies.interest', 'partner_hobbies_rel', 'partner_ids', 'hobbies_ids', string='Hobbies and Interests', tracking=True)
    revenue_source = fields.Char('Revenue Source/Income', tracking=True)
    term_goals = fields.Char('Personal plan/Term goals', tracking=True)
    social_influence = fields.Char('Social Influence', tracking=True)
    behavior_on_the_internet = fields.Char('Behavior on the Internet', tracking=True)
    affected_by = fields.Selection(
        [('family', 'Family'), ('friend', 'Friend'), ('co_worker', 'Co-Worker'), ('community', 'Community'),
         ('electronic_media', 'Electronic media'), ('other', 'Other')], string='Affected by...', tracking=True)
    work_start_time = fields.Float('Work start time', tracking=True)
    work_end_time = fields.Float('Work end time', tracking=True)
    break_start_time = fields.Float('Break start time', tracking=True)
    break_end_time = fields.Float('Break end time', tracking=True)
    transport = fields.Selection(
        [('bicycle', 'Bicycle'), ('scooter', 'Scooter'), ('bus', 'Bus'), ('car', 'Car'), ('other', 'Other')], string='Transport', tracking=True)
    pain_point_and_desires = fields.One2many('pain.point.and.desires', 'partner_id', string='Pain point and desires', tracking=True)
    pain_point = fields.One2many('pain.point.and.desires', 'partner_id', string='Pain point', domain=[('type', '=', 'pain_point')], tracking=True)
    desires = fields.One2many('pain.point.and.desires', 'partner_id', string='Desires', domain=[('type', '=', 'desires')], tracking=True)
    persona = fields.One2many('customer.persona', 'partner_id', 'Chân dung khách hàng')

