# -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

from openerp.osv import osv
from openerp.report import report_sxw


class Session(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Session, self).__init__(cr, uid, name, context=context)

        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        company_id = user.company_id
        self.tip = 0
        self.service = 0
        self.discount = 0
        self.discount100 = 0
        self.subtotal = 0
        self.localcontext.update({
            'company': company_id or False,
            # 'products': self._get_products,
            'areas': self._get_areas,
            'summary': self.summary,
        })

    def summary(self):
        res = {
            'tip': self.tip,
            'discount': self.discount,
            'discount100': self.discount100,
            'service': self.service,
            'subtotal': self.subtotal,
            'net_sale': self.subtotal - self.discount - self.discount100,
            'total': self.subtotal - self.discount - self.discount100 + self.service + self.tip
        }
        return res

    def process_order(self, order, products, service_id, discount_id, tip_product_id):
        for line in order.lines:
            if line.product_id.id not in [service_id, discount_id, tip_product_id]:
                flag = False
                for p in products:
                    if line.product_id.name == p['name']:
                        p['qty'] += int(line.qty)
                        p['subtotal'] += line.price_unit * line.qty
                        flag = True
                        break
                if not flag:
                    new = {
                        'name': line.product_id.name,
                        'area': line.product_id.area_id.name,
                        'qty': int(line.qty),
                        'subtotal': line.price_unit * line.qty
                    }
                    products.append(new)

                self.subtotal += line.price_unit * line.qty
        if order.discount_pc == 100:
            self.discount100 += abs(order.total_discount)
        else:
            self.discount += abs(order.total_discount)
        self.service += order.service_fee
        self.tip += order.tip

    def _get_products(self):
        products = []
        for s in self.pool.get('pos.session').browse(self.cr, self.uid, self.ids):
            if s.config_id.tip_product_id:
                tip_product_id = s.config_id.tip_product_id.id
            else:
                tip_product_id = 0
            if s.config_id.service_product_id:
                service_product_id = s.config_id.service_product_id.id
            else:
                service_product_id = 0
            if s.config_id.discount_product_id:
                discount_product_id = s.config_id.discount_product_id.id
            else:
                discount_product_id = 0
            for order in s.order_ids:
                if order.state != 'cancel':
                    self.process_order(order, products, service_product_id, discount_product_id, tip_product_id)
        return products

    def _get_areas(self):
        areas = []
        for product in self._get_products():
            flag = False
            for c in areas:
                if c['name'] == product['area']:
                    c['products'].append(product)
                    c['total'] += product['subtotal']
                    flag = True
                    break
            if not flag:
                new = {
                    'name': product['area'],
                    'products': [product],
                    'total': product['subtotal']
                }
                areas.append(new)
        return areas


class ReportSessionReceipt(osv.AbstractModel):
    _name = 'report.pos_restaurant_report.report_session_receipt'
    _inherit = 'report.abstract_report'

    _template = 'pos_restaurant_report.report_session_receipt'
    _wrapped_report_class = Session
