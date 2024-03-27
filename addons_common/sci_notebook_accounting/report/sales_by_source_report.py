from odoo import fields, models, api, tools, _
import datetime


class SaleBySourceReport(models.Model):
    _name = 'sales.by.source.report'
    _auto = False
    _description = 'Báo cáo doanh số theo nguồn tab01'

    name = fields.Char(string='Mã phiếu')
    date = fields.Date(string='Ngày ghi nhận')
    company_id = fields.Many2one(comodel_name='res.company', string='Chi nhánh')
    brand_id = fields.Many2one(comodel_name='res.brand', string='Thương hiệu')
    # category_source = fields.Many2one(comodel_name='crm.category.source', string='Nhóm nguồn')
    # category_source_utm = fields.Many2one(comodel_name='utm.source', string='Nguồn')
    text_category_source = fields.Char(string='Nhóm nguồn')
    text_category_source_utm = fields.Char(string='nguồn')
    amount_source = fields.Integer(string='Tổng tiền theo nguồn', default=0.0)
    type = fields.Selection(string='Loại doanh thu',
                            selection=[('01', 'Doanh thu thực hiện'), ('02', 'Doanh thu kế hoạch')])

    # currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'sales_by_source_report')
        self._cr.execute("""
            CREATE or REPLACE view sales_by_source_report as(
            SELECT
                line.id as id,
                head.name as name,
                head.date as date,
                head.company_id as company_id,
                head.brand_id as brand_id,
                line.text_category_source as text_category_source,
                line.text_category_source_utm as text_category_source_utm,
                CASE
                    WHEN line.is_refund = 'False' or line.is_refund is null
                    THEN line.amount_source
                    ELSE -1 * line.amount_source
                END
                AS amount_source,
                head.type as type
            FROM sale_by_source_line as line
            LEFT JOIN sales_by_source as head ON line.sale_source_id = head.id
            WHERE head.state in ('posted', 'locked') and head.id is not null
            )""",)


class SaleByServiceReport(models.Model):
    _name = 'sales.by.service.report'
    _auto = False
    _description = 'Báo cáo doanh số theo dịch vụ tab02'

    name = fields.Char(string='Mã phiếu')
    date = fields.Date(string='Ngày ghi nhận')
    company_id = fields.Many2one(comodel_name='res.company', string='Chi nhánh')
    brand_id = fields.Many2one(comodel_name='res.brand', string='Thương hiệu')
    service_type = fields.Selection(
        [('01', 'Spa'), ('02', 'Laser'), ('03', 'Nha'), ('04', 'Phẫu thuật'), ('05', 'Chi phí khác')],
        string='Loại dịch vụ')
    # service_catge = fields.Many2one(comodel_name='sh.medical.health.center.service.category', string='Nhóm dịch vụ')
    service_catge = fields.Char(string='Nhóm dịch vụ')
    amount_service = fields.Integer(string='Tổng tiền theo nguồn', default=0.0)

    # currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'sales_by_service_report')
        self._cr.execute("""
            CREATE or REPLACE view sales_by_service_report as(
            SELECT
                line.id as id,
                head.name as name,
                head.date as date,
                head.company_id as company_id,
                head.brand_id as brand_id,
                line.service_type as service_type,
                line.service_catge as service_catge,
                CASE
                    WHEN line.is_refund = 'False' or line.is_refund is null
                    THEN line.amount_service
                    ELSE -1 * line.amount_service
                END
                AS amount_service
            FROM sale_by_source_line as line
            LEFT JOIN sales_by_source as head ON line.sale_service_id = head.id
            WHERE head.state in ('posted', 'locked') and head.id is not null
            )""")


class SaleByRevenueReport(models.Model):
    _name = 'sales.by.revenue.report'
    _auto = False
    _description = 'Báo cáo doanh số theo nguồn bán tab03'

    name = fields.Char(string='Mã phiếu')
    date = fields.Date(string='Ngày ghi nhận')
    company_id = fields.Many2one(comodel_name='res.company', string='Chi nhánh')
    brand_id = fields.Many2one(comodel_name='res.brand', string='Thương hiệu')
    revenue_ids = fields.Many2one(comodel_name='config.source.revenue', string='Nhóm nguồn doanh thu')
    amount_revenue = fields.Integer(string='Tổng tiền theo nguồn bán')

    # currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'sales_by_revenue_report')
        self._cr.execute("""
            CREATE or REPLACE view sales_by_revenue_report as(
            SELECT
                line.id as id,
                head.name as name,
                head.date as date,
                head.company_id as company_id,
                head.brand_id as brand_id,
                line.revenue_ids as revenue_ids,
                CASE
                    WHEN line.is_refund = 'False' or line.is_refund is null
                    THEN line.amount_revenue
                    ELSE -1 * line.amount_revenue
                END
                AS amount_revenue
            FROM sale_by_source_line as line
            LEFT JOIN sales_by_source as head ON line.sale_revenue_id = head.id
            WHERE head.state in ('posted', 'locked') and head.id is not null
            )""")


class SaleByCostReport(models.Model):
    _name = 'sales.by.cost.report'
    _auto = False
    _description = 'Báo cáo doanh số theo nhóm chi phí tab04'

    name = fields.Char(string='Mã phiếu')
    date = fields.Date(string='Ngày ghi nhận')
    company_id = fields.Many2one(comodel_name='res.company', string='Chi nhánh')
    brand_id = fields.Many2one(comodel_name='res.brand', string='Thương hiệu')
    cost_source_ids = fields.Many2one(comodel_name='source.config.account', string='Nguồn/khối')
    cost_items_ids = fields.Many2one(comodel_name='cost.item.config', string='Nhóm chi phí',
                                     domain="[('source', '=', cost_source_ids)]")
    amount_cost = fields.Integer(string='Tổng tiền theo hạng mục chi phí')

    # currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'sales_by_cost_report')
        self._cr.execute("""
            CREATE or REPLACE view sales_by_cost_report as(
            SELECT
                line.id as id,
                head.name as name,
                head.date as date,
                head.company_id as company_id,
                head.brand_id as brand_id,
                line.cost_source_ids as cost_source_ids,
                line.cost_items_ids as cost_items_ids,
                CASE
                    WHEN line.is_refund = 'False' or line.is_refund is null
                    THEN line.amount_cost
                    ELSE -1 * line.amount_cost
                END
                AS amount_cost
            FROM sale_by_source_line as line
            LEFT JOIN sales_by_source as head ON line.sale_cost_id = head.id
            WHERE head.state in ('posted', 'locked') and head.id is not null
            )""")


class CompareByDate(models.Model):
    _name = 'compare.by.date.report'
    _auto = False
    _description = 'So sánh doanh số theo ngày'

    date = fields.Date(string='Ngày tháng')
    amount = fields.Integer(string='Doanh số')
    company = fields.Many2one('res.company', string='Công ty')
    growth = fields.Float(string='Tăng trưởng (%)', digits=(3, 2))

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'compare_by_date_report')
        self._cr.execute("""
            CREATE or REPLACE view compare_by_date_report as(
            WITH data AS(
            SELECT
                id,
                date,
                company_id,
                sum(amount_subtotal_source) as amount
            FROM sales_by_source
            WHERE type = '01'
            GROUP BY id, date, company_id
            ORDER BY date, company_id)

            , previous_data AS(
            SELECT
                source.id,
                source.date -1 as previous_date,
                source.company_id,
                sum(data.amount) as amount
            FROM sales_by_source as source
            LEFT JOIN data ON source.date -1 = data.date and source.company_id = data.company_id 
            WHERE type = '01'
            GROUP BY source.id, source.date-1, source.company_id
            ORDER BY source.date-1, source.company_id)

            SELECT
                data.id, 
                data.company_id as company, 
                data.date, 
                data.amount,
            CASE
                WHEN previous_data.amount <> 0 THEN
                    (data.amount - previous_data.amount)/previous_data.amount * 100
                ELSE
                    0.0
            END  as growth
            FROM data
            LEFT JOIN previous_data ON data.date -1 = previous_data.previous_date and data.company_id = previous_data.company_id
            ORDER BY data.company_id, data.date
            )""")
