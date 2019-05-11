#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class POSSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def print_session_receipt(self):
        return self.env['report'].get_action(self, 'pos_restaurant_report.report_session_receipt')

    @api.multi
    def report_get_info(self):
        orders = self.mapped('order_ids')

        session_info = {
            'total_customers': sum(self.mapped('customers_count')),
            'total_orders': len(orders),
            'total_cost': round(sum(self.mapped('session_cost')), 2),
            'total_bank': round(sum(self.mapped('bank_sale')), 2),
            'total_cash': round(sum(self.mapped('cash_sale')), 2),
            'total_sale': round(sum(self.mapped('customers_count')), 2),
            'total_discount': abs(sum(self.mapped('total_discount'))),
            'total_service': sum(self.mapped('service_fee')),
            'total_tips': sum(self.mapped('tip')),
            'allow_discount': sum(self.mapped('iface_global_discount')),
            'allow_service': sum(self.mapped('iface_service_fee')),
            'allow_tip': sum(self.mapped('iface_allow_tip')),
            'pos_list': self.mapped('config_id'),
            # 'currency_id': self.env['res.company']._company_default_get('pos.session').currency_id
        }

        partner_list = orders.mapped('partner_id')
        partner_stats = []
        for p in partner_list:
            p_orders = orders.filtered(lambda r: r.partner_id.id == p.id)
            partner_stats.append({
                'name': p.name,
                'orders': len(p_orders),
                'customers': sum(p_orders.mapped('customer_count')),
                'cost': round(sum(p_orders.mapped('order_cost')), 2),
                'sale': round(sum(p_orders.mapped('total_sale')), 2),
                'tip': sum(p_orders.mapped('tip')),
                'service': sum(p_orders.mapped('service_fee')),
                'discount': abs(sum(p_orders.mapped('total_discount'))),
            })

        waiter_list = orders.mapped('waiter_id')
        waiter_stats = []
        for w in waiter_list:
            w_orders = orders.filtered(lambda r: r.waiter_id.id == w.id)
            waiter_stats.append({
                'name': w.name,
                'orders': len(w_orders),
                'customers': sum(w_orders.mapped('customer_count')),
                'sale': sum(w_orders.mapped('total_sale')),
                'tip': sum(w_orders.mapped('tip')),
                'service': sum(w_orders.mapped('service_fee')),
                'discount': abs(sum(w_orders.mapped('total_discount'))),
            })

        line_list = orders.mapped('lines')
        product_list = line_list.mapped('product_id')
        garnished_lines = line_list.filtered(lambda r: r.product_garnish_ids)
        all_garnish_products = garnished_lines.mapped('product_garnish_ids.garnish_id')
        area_list = product_list.mapped('area_id')
        products_by_area = []
        for area in area_list:
            product_stats = []
            for product in product_list.filtered(lambda r: r.area_id.id == area.id):
                lines_product = line_list.filtered(lambda r: r.product_id.id == product.id)
                lines_garnished = lines_product.filtered(lambda r: r.product_garnish_ids)
                garnish_products = lines_garnished.mapped('product_garnish_ids.garnish_id')
                product_garnish_stats = dict([(x.id, {'name': x.name, 'qty': 0}) for x in garnish_products])
                for line in lines_garnished:
                    for garnish in line.product_garnish_ids:
                        product_garnish_stats[garnish.garnish_id.id]['qty'] += int(line.qty)

                product_stats.append({
                    'name': product.name,
                    'orders': len(lines_product.mapped('order_id')),
                    'qty': int(sum(lines_product.mapped('qty'))),
                    'cost': round(sum(lines_product.mapped('cost_price')), 2),
                    'sale': sum(lines_product.mapped('base_price')),
                    'garnish': list(product_garnish_stats.itervalues()),
                })

            area_garnish = all_garnish_products.filtered(lambda r: r.area_id.id == area.id)
            all_garnish_stats = dict([(x.id, {'name': x.name, 'qty': 0}) for x in area_garnish])
            for line in garnished_lines:
                for garnish in line.product_garnish_ids:
                    if garnish.garnish_id.id in all_garnish_stats:
                        all_garnish_stats[garnish.garnish_id.id]['qty'] += int(line.qty)
            products_by_area.append({
                'name': area.name,
                'products': product_stats,
                'garnishes': list(all_garnish_stats.itervalues()),
            })

        return {
            'session_info': session_info,
            'partner_stats': partner_stats,
            'waiter_stats': waiter_stats,
            'product_stats': products_by_area,
        }
