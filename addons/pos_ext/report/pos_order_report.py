# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import tools
from openerp.osv import fields, osv

_logger = logging.getLogger(__name__)

WEEK_DAYS = [
    ('1', 'Monday'),
    ('2', 'Tuesday'),
    ('3', 'Wednesday'),
    ('4', 'Thursday'),
    ('5', 'Friday'),
    ('6', 'Saturday'),
    ('7', 'Sunday')
]


class POSOrderReport(osv.osv):
    _inherit = "report.pos.order"

    _columns = {
        'date': fields.date('Date Order', readonly=True),
        'week_day': fields.selection(WEEK_DAYS, 'Weekday', readonly=True),
        'month_day': fields.char('Month Day', readonly=True),
        'day_hour': fields.char('Day Hour', readonly=True),
    }

    def _select(self):
        select_str = """
            min(l.id) as id,
            count(*) as nbr,
            s.date as date,
            s.week_day as week_day,
            s.month_day as month_day,
            s.day_hour as day_hour,
            sum(l.qty * u.factor) as product_qty,
            sum(l.qty * l.price_unit) as price_sub_total,
            sum((l.qty * l.price_unit) * (100 - l.discount) / 100) as price_total,
            sum((l.qty * l.price_unit) * (l.discount / 100)) as total_discount,
            (sum(l.qty*l.price_unit)/sum(l.qty * u.factor))::decimal as average_price,
            sum(cast(to_char(date_trunc('day',s.date_order) - date_trunc('day',s.create_date),'DD') as int)) as delay_validation,
            s.partner_id as partner_id,
            s.state as state,
            s.user_id as user_id,
            s.location_id as location_id,
            s.company_id as company_id,
            s.sale_journal as journal_id,
            l.product_id as product_id,
            pt.categ_id as product_categ_id,
            p.product_tmpl_id,
            ps.config_id,
            pt.pos_categ_id,
            pc.stock_location_id,
            s.pricelist_id,
            s.invoice_id IS NOT NULL AS invoiced
        """
        return select_str

    def _from(self):
        from_str = """
            pos_order_line as l
            left join pos_order s on (s.id=l.order_id)
            left join product_product p on (l.product_id=p.id)
            left join product_template pt on (p.product_tmpl_id=pt.id)
            left join product_uom u on (u.id=pt.uom_id)
            left join pos_session ps on (s.session_id=ps.id)
            left join pos_config pc on (ps.config_id=pc.id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            s.date,
            s.week_day,
            s.month_day,
            s.day_hour,
            s.partner_id,
            s.state,
            pt.categ_id,
            s.user_id,
            s.location_id,
            s.company_id,
            s.sale_journal,
            s.pricelist_id,
            s.invoice_id,
            l.product_id,
            s.create_date,
            pt.categ_id,
            pt.pos_categ_id,
            p.product_tmpl_id,
            ps.config_id,
            pc.stock_location_id
        """
        return group_by_str

    def _having(self):
        having_str = """
            sum(l.qty * u.factor) != 0
        """
        return having_str

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT %s
            FROM %s
            GROUP BY %s
            HAVING %s
            )""" % (self._table, self._select(), self._from(), self._group_by(), self._having()))
