#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import api, fields, models, _

_logger = logging.getLogger(__name__)


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    pos_session_id = fields.Many2one('pos.session', string="Session", related='statement_id.pos_session_id', store=True)
    reason_id = fields.Many2one('cash.box.reason', string="Reason")
    reason_category_id = fields.Many2one('cash.box.reason.category', string="Reason Category",
                                         related='reason_id.category_id', store=True)

    @api.model
    def create(self, vals):
        stmt = self.env['account.bank.statement'].browse(vals['statement_id'])
        if stmt.pos_session_id:
            vals.update({'date': stmt.pos_session_id.start_at})
            if vals.get('account_id', False) and not vals.get('journal_id', False):
                if vals['amount'] < 0 and stmt.journal_id.loss_account_id.id == vals['account_id']:
                    reason = stmt.pos_session_id.config_id.cash_diff_loss_reason_id
                    vals.update({
                        'reason_id': reason.id
                    })
                elif vals['amount'] > 0 and stmt.journal_id.profit_account_id.id == vals['account_id']:
                    reason = stmt.pos_session_id.config_id.cash_diff_profit_reason_id
                    vals.update({
                        'reason_id': reason.id
                    })
            elif vals.get('pos_statement_id', False) and vals.get('journal_id', False):
                # order = self.env['pos.order'].browse(vals['pos_statement_id'])
                journal = self.env['account.journal'].browse(vals['journal_id'])
                if journal.type == 'cash':
                    if not vals.get('reason_id', False) and vals['amount'] < 0:
                        vals.update({
                            'reason_id': journal.default_out_reason_id.id
                        })
        return super(AccountBankStatementLine, self).create(vals)

    def fix_reason_id(self, cr, uid, **args):
        mod_obj = self.pool.get('ir.model.data')
        reason_profit = mod_obj.get_object_reference(cr, uid, 'pos_cash_control', 'cash_difference_profit')[1]
        reason_loss = mod_obj.get_object_reference(cr, uid, 'pos_cash_control', 'cash_difference_loss')[1]
        reason_income = mod_obj.get_object_reference(cr, uid, 'pos_cash_control', 'sales_cash_payment')[1]
        reason_outcome = mod_obj.get_object_reference(cr, uid, 'pos_cash_control', 'sales_cash_change')[1]
        reason_voucher_income = mod_obj.get_object_reference(cr, uid, 'pos_cash_control', 'sales_voucher_payment')[1]
        reason_voucher_outcome = mod_obj.get_object_reference(cr, uid, 'pos_cash_control', 'voucher_to_cash')[1]
        reason_tip = mod_obj.get_object_reference(cr, uid, 'pos_cash_control', 'sales_customers_tips')[1]
        reason_discount = mod_obj.get_object_reference(cr, uid, 'pos_cash_control', 'sales_customers_discounts')[1]
        reason_house_discount = mod_obj.get_object_reference(cr, uid, 'pos_cash_control', 'sales_house_discounts')[1]

        # lines_ids = self.search(cr, uid, [('reason_id', '=', reason_discount)])
        # lines = self.browse(cr, uid, lines_ids)
        # for line in lines:
        #     order_id = self.pool.get('pos.order').browse(cr, uid, line.pos_statement_id.id)
        #     if order_id.discount_pc == 100:
        #         self.write(cr, uid, line.id, {'reason_id': reason_house_discount})

        # lines_ids = self.search(cr, uid, [('pos_session_id', '!=', False)])
        # lines = self.browse(cr, uid, lines_ids)
        # for line in lines:
        #     session_id = self.pool.get('pos.session').browse(cr, uid, line.pos_session_id.id)
        #     self.write(cr, uid, line.id, {'date': session_id.start_at})
        #
        # lines_ids = self.search(cr, uid, [('pos_session_id', '!=', False), ('pos_statement_id', '=', False)])
        # lines = self.browse(cr, uid, lines_ids)
        # for line in lines:
        #     reason_id = self.pool.get('cash.box.reason').search(cr, uid, [('name', '=', line.name)])
        #     if reason_id:
        #         self.write(cr, uid, line.id, {'reason_id': reason_id[0]})
        #     elif not line.ref:
        #         if line.amount > 0:
        #             self.write(cr, uid, line.id, {'reason_id': reason_profit})
        #         else:
        #             self.write(cr, uid, line.id, {'reason_id': reason_loss})
        #
        # lines_ids = self.search(cr, uid, [('pos_statement_id', '!=', False)])
        # lines = self.browse(cr, uid, lines_ids)
        # for line in lines:
        #     if line.amount > 0:
        #         journal = self.pool.get('account.journal').browse(cr, uid, line.journal_id.id)
        #         if journal.type == 'cash':
        #             self.write(cr, uid, line.id, {'reason_id': reason_income})
        #         else:
        #             session_id = self.pool.get('pos.session').browse(cr, uid, line.pos_session_id.id)
        #             stmt_id = self.pool.get("account.bank.statement").search(cr, uid, [
        #                 ('pos_session_id', '=', session_id.id),
        #                 ('journal_id', '=', session_id.cash_journal_id.id)])[0]
        #             self.create(cr, uid, {
        #                 'date': session_id.start_at,
        #                 'amount': line.amount,
        #                 'name': _('Ventas por Voucher'),
        #                 'statement_id': stmt_id,
        #                 'pos_statement_id': line.pos_statement_id.id,
        #                 'reason_id': reason_voucher_income,
        #             })
        #             self.create(cr, uid, {
        #                 'date': session_id.start_at,
        #                 'amount': - line.amount,
        #                 'name': _('Voucher por cobrar'),
        #                 'statement_id': stmt_id,
        #                 'pos_statement_id': line.pos_statement_id.id,
        #                 'reason_id': reason_voucher_outcome,
        #             })
        #
        #     else:
        #         self.write(cr, uid, line.id, {'reason_id': reason_outcome})
        # sessions_ids = self.pool.get('pos.session').search(cr, uid, [])
        # for session in self.pool.get('pos.session').browse(cr, uid, sessions_ids):
        #     stmt_id = self.pool.get("account.bank.statement").search(cr, uid, [
        #                     ('pos_session_id', '=', session.id),
        #                     ('journal_id', '=', session.cash_journal_id.id)])[0]
        #     for order in session.order_ids:
        #         if order.tip:
        #             self.create(cr, uid, {
        #                 'date': session.start_at,
        #                 'amount': - order.tip,
        #                 'name': _('Quita propina de venta'),
        #                 'statement_id': stmt_id,
        #                 'pos_statement_id': order.id,
        #                 'reason_id': reason_income,
        #             })
        #             self.create(cr, uid, {
        #                 'date': session.start_at,
        #                 'amount': order.tip,
        #                 'name': _('Propina de venta'),
        #                 'statement_id': stmt_id,
        #                 'pos_statement_id': order.id,
        #                 'reason_id': reason_tip,
        #             })
        #         if order.total_discount:
        #             self.create(cr, uid, {
        #                 'date': session.start_at,
        #                 'amount': - order.total_discount,
        #                 'name': _('Suma descuenta a la venta'),
        #                 'statement_id': stmt_id,
        #                 'pos_statement_id': order.id,
        #                 'reason_id': reason_income,
        #             })
        #             self.create(cr, uid, {
        #                 'date': session.start_at,
        #                 'amount': order.total_discount,
        #                 'name': _('Descuento de clientes'),
        #                 'statement_id': stmt_id,
        #                 'pos_statement_id': order.id,
        #                 'reason_id': reason_discount,
        #             })



class POSSession(models.Model):
    _inherit = 'pos.session'

    cash_operations = fields.One2many('account.bank.statement.line', 'pos_session_id', string='Cash Operations',
                                      domain=[('journal_id.type', '=', 'cash')])
