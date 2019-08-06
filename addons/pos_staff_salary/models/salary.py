#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _


class POSConfig(models.Model):
    _inherit = 'pos.config'

    iface_staff_salary = fields.Boolean(string='Staff Salary',
                                        help='Calculate Staff Salary')
    salary_pc = fields.Float(string='Salary Percentage', default=10,
                             help='The default salary percentage')
    exclude_discounts = fields.Boolean("Exclude discounts",
                                       help="Don't include discounted orders in Salary claculation.")
    exclude_products = fields.Many2many(comodel_name='product.product', string='Excluded products',
                                        help="These products won't be included in salary calculation.")


class POSSession(models.Model):
    _inherit = 'pos.session'

    staff_salary = fields.Float(string='Staff Salary', compute='_compute_salary',
                                help='The calculated staff salary.', store=True)

    iface_staff_salary = fields.Boolean(related='config_id.iface_staff_salary')

    @api.multi
    @api.depends('order_ids', 'order_ids.lines')
    def _compute_salary(self):
        for session in self:
            if session.iface_staff_salary:
                subtotal = 0
                orders = session.order_ids
                excluded_products_ids = session.config_id.exclude_products.ids
                if session.config_id.exclude_discounts:
                    orders = orders.filtered(lambda r: r.total_discount == 0)
                for line in orders.mapped('lines'):
                    if line.product_id.id not in excluded_products_ids:
                        subtotal += line.base_price
                session.staff_salary = subtotal * session.config_id.salary_pc / 100
