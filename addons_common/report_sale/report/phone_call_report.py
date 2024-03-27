from odoo import fields, models, tools

chua_xu_ly = ('draft', 'not_connect', 'later', 'not_connect_1')
da_xu_ly = ('connected', 'duplicate', 'zalo', 'sms', 'connected_2', 'later_1', 'cancelled', 'before', 'connected_1',
            'not_connect_1')
sai_so = 'error_phone'
GROUP_REPORT_CHECK = ('Surgery', 'Laser', 'Spa', 'Odontology', 'Other')
type_pc = ('Potential', 'Check', 'Check1', 'Check2', 'Check3', 'Check8', 'Check4', 'Check5', 'Check6', 'Change', 'Change1', 'Change2', 'Change3', 'Change4', 'ReCheck4', 'ReCheck5', 'ReCheck6', 'ReCheck7', 'ReCheck8', 'ReCheck9', 'ReCheck', 'ReCheck1', 'ReCheck2', 'ReCheck3', 'ReCheck10')
NOTE = [
        ('Check', 'Chăm sóc lần 1'),
        ('Check1', 'Chăm sóc lần 2'),
        ('Check2', 'Chăm sóc lần 3'),
        ('Check3', 'Chăm sóc lần 4'),
        ('Check8', 'Chăm sóc lần 5'),
        ('Check4', 'Chăm sóc kết thúc liệu trình 1'),
        ('Check5', 'Chăm sóc kết thúc liệu trình 2'),
        ('Check6', 'Chăm sóc kết thúc liệu trình 3'),
        ('Change', 'Thay băng lần 1'),
        ('Change1', 'Thay băng lần 2'),
        ('Change2', 'Thay băng lần 3'),
        ('Change3', 'Thay băng lần 4'),
        ('Change4', 'Thay băng lần 5'),
        ('ReCheck4', 'Tái khám lần 1'),
        ('ReCheck5', 'Tái khám lần 2'),
        ('ReCheck6', 'Tái khám lần 3'),
        ('ReCheck7', 'Tái khám lần 4'),
        ('ReCheck8', 'Tái khám lần 5'),
        ('ReCheck9', 'Tái khám định kì'),
        ('ReCheck', 'Cắt chỉ'),
        ('ReCheck1', 'Hút dịch'),
        ('ReCheck2', 'Rút ống mũi'),
        ('ReCheck3', 'Thay nẹp mũi'),
        ('ReCheck10', 'Nhắc liệu trình'),
        ('Potential', 'Khai thác dịch vụ tiềm năng')
    ]

class PhoneCallReport(models.Model):
    _name = 'report.phone.call.source'
    _auto = False
    _description = 'Báo cáo phone call'

    state = fields.Selection([('chua_xu_ly', 'Chưa xử lý'), ('da_xu_ly', 'Đã xử lý'), ('sai_so', 'Sai số'), ('other', 'Khác')],
                             'Trạng thái')
    service = fields.Selection([
        ('Surgery', 'Phẫu thuật'),
        ('Laser', 'Laser'),
        ('Spa', 'Spa'),
        ('Odontology', 'Nha khoa'),
        ('Other', 'Khác')
    ], 'Loại dịch vụ')
    type_pc = fields.Selection(NOTE)
    date_call = fields.Datetime('Ngày gọi')
    brand_id = fields.Many2one('res.brand', 'Thương hiệu')
    company_id = fields.Many2one('res.company', 'Chi nhánh')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'report_phone_call_source')
        self._cr.execute("""
            CREATE or REPLACE view report_phone_call_source as(
            SELECT
                id as id,
                group_report as service,
                CASE
                    WHEN state in %s 
                    THEN 'chua_xu_ly'
                    WHEN state in %s 
                    THEN 'da_xu_ly'
                    WHEN state = '%s'
                    THEN 'sai_so'
                    ELSE 'other'
                END
                AS state,
                type_pc as type_pc,
                call_date as date_call,
                brand_id as brand_id,
                company_id as company_id
            FROM crm_phone_call
            where group_report in %s and type_pc in %s
            )""" % (chua_xu_ly, da_xu_ly, sai_so, GROUP_REPORT_CHECK, type_pc))


class PhoneCallReportSpa(models.Model):
    _name = 'report.phone.call.source.spa'
    _auto = False
    _description = 'Báo cáo phone call Spa'

    state = fields.Selection([('chua_xu_ly', 'Chưa xử lý'), ('da_xu_ly', 'Đã xử lý'), ('sai_so', 'Sai số')],
                             'Trạng thái')
    type_pc = fields.Selection(NOTE)
    date_call = fields.Datetime('Ngày gọi')
    brand_id = fields.Many2one('res.brand', 'Thương hiệu')
    company_id = fields.Many2one('res.company', 'Chi nhánh')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'report_phone_call_source_spa')
        self._cr.execute("""
            CREATE or REPLACE view report_phone_call_source_spa as(
            SELECT
                id as id,
                CASE
                    WHEN state in %s 
                    THEN 'chua_xu_ly'
                    WHEN state in %s 
                    THEN 'da_xu_ly'
                    WHEN state = '%s'
                    THEN 'sai_so'
                    ELSE 'other'
                END
                AS state,
                type_pc as type_pc,
                call_date as date_call,
                brand_id as brand_id,
                company_id as company_id
            FROM crm_phone_call
            where group_report = 'Spa' and type_pc in %s
            )""" % (chua_xu_ly, da_xu_ly, sai_so, type_pc))


class PhoneCallReportLaser(models.Model):
    _name = 'report.phone.call.source.laser'
    _auto = False
    _description = 'Báo cáo phone call laser'

    state = fields.Selection([('chua_xu_ly', 'Chưa xử lý'), ('da_xu_ly', 'Đã xử lý'), ('sai_so', 'Sai số')],
                             'Trạng thái')
    type_pc = fields.Selection(NOTE)
    date_call = fields.Datetime('Ngày gọi')
    brand_id = fields.Many2one('res.brand', 'Thương hiệu')
    company_id = fields.Many2one('res.company', 'Chi nhánh')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'report_phone_call_source_laser')
        self._cr.execute("""
            CREATE or REPLACE view report_phone_call_source_laser as(
            SELECT
                id as id,
                CASE
                    WHEN state in %s 
                    THEN 'chua_xu_ly'
                    WHEN state in %s 
                    THEN 'da_xu_ly'
                    WHEN state = '%s'
                    THEN 'sai_so'
                    ELSE 'other'
                END
                AS state,
                type_pc as type_pc,
                call_date as date_call,
                brand_id as brand_id,
                company_id as company_id
            FROM crm_phone_call
            where group_report = 'Laser' and type_pc in %s
            )""" % (chua_xu_ly, da_xu_ly, sai_so, type_pc))


class PhoneCallReportSurgery(models.Model):
    _name = 'report.phone.call.source.surgery'
    _auto = False
    _description = 'Báo cáo phone call surgery'

    state = fields.Selection([('chua_xu_ly', 'Chưa xử lý'), ('da_xu_ly', 'Đã xử lý'), ('sai_so', 'Sai số')],
                             'Trạng thái')
    type_pc = fields.Selection(NOTE)
    date_call = fields.Datetime('Ngày gọi')
    brand_id = fields.Many2one('res.brand', 'Thương hiệu')
    company_id = fields.Many2one('res.company', 'Chi nhánh')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'report_phone_call_source_surgery')
        self._cr.execute("""
            CREATE or REPLACE view report_phone_call_source_surgery as(
            SELECT
                id as id,
                CASE
                    WHEN state in %s 
                    THEN 'chua_xu_ly'
                    WHEN state in %s 
                    THEN 'da_xu_ly'
                    WHEN state = '%s'
                    THEN 'sai_so'
                    ELSE 'other'
                END
                AS state,
                type_pc as type_pc,
                call_date as date_call,
                brand_id as brand_id,
                company_id as company_id
            FROM crm_phone_call
            where group_report = 'Surgery' and type_pc in %s
            )""" % (chua_xu_ly, da_xu_ly, sai_so, type_pc))


class PhoneCallReportOdontology(models.Model):
    _name = 'report.phone.call.source.odontology'
    _auto = False
    _description = 'Báo cáo phone call odontology'

    state = fields.Selection([('chua_xu_ly', 'Chưa xử lý'), ('da_xu_ly', 'Đã xử lý'), ('sai_so', 'Sai số')],
                             'Trạng thái')
    type_pc = fields.Selection(NOTE)
    date_call = fields.Datetime('Ngày gọi')
    brand_id = fields.Many2one('res.brand', 'Thương hiệu')
    company_id = fields.Many2one('res.company', 'Chi nhánh')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'report_phone_call_source_odontology')
        self._cr.execute("""
            CREATE or REPLACE view report_phone_call_source_odontology as(
            SELECT
                id as id,
                CASE
                    WHEN state in %s 
                    THEN 'chua_xu_ly'
                    WHEN state in %s 
                    THEN 'da_xu_ly'
                    WHEN state = '%s'
                    THEN 'sai_so'
                    ELSE 'other'
                END
                AS state,
                type_pc as type_pc,
                call_date as date_call,
                brand_id as brand_id,
                company_id as company_id
            FROM crm_phone_call
            where group_report = 'Odontology' and type_pc in %s
            )""" % (chua_xu_ly, da_xu_ly, sai_so, type_pc))
