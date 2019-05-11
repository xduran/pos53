#  -*- coding: utf-8 -*-
# Part of Odec Suite. See LICENSE file for full copyright and licensing details.

import logging
from openerp import tools, api, fields, models, _
from openerp.osv import fields as old_fields
from openerp.exceptions import UserError
import time
from datetime import datetime


_logger = logging.getLogger(__name__)


class CashBoxReasonCategory(models.Model):
    _name = 'cash.box.reason.category'
    _order = 'sequence asc'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence')


class CashBoxReason(models.Model):
    _name = 'cash.box.reason'
    _order = 'category_id,sequence asc'

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence')
    description = fields.Text(string='Description')
    cash_box_in = fields.Boolean(string='In', default=False)
    cash_box_out = fields.Boolean(string='Out', default=False)
    category_id = fields.Many2one('cash.box.reason.category', string='Category')


class POSConfig(models.Model):
    _inherit = 'pos.config'

    cash_diff_profit_reason_id = fields.Many2one('cash.box.reason', string='Profit Reason')
    cash_diff_loss_reason_id = fields.Many2one('cash.box.reason', string='Loss Reason')
    service_fee_reason_id = fields.Many2one('cash.box.reason', string='Service Reason')
    discount_reason_id = fields.Many2one('cash.box.reason', string='Discount Reason')
    house_discount_reason_id = fields.Many2one('cash.box.reason', string='House Tab Reason')
    tip_reason_id = fields.Many2one('cash.box.reason', string='Tip Reason')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    default_in_reason_id = fields.Many2one('cash.box.reason', string='In Reason')
    default_out_reason_id = fields.Many2one('cash.box.reason', string='Out Reason')


class POSOrder(models.Model):
    _inherit = 'pos.order'

    def _process_order_payments(self, cr, uid, order, context=None):
        stmts = []
        for stmt in order['statement_ids']:
            found = False
            for item in stmts:
                if stmt[2]['journal_id'] == item[2]['journal_id'] \
                        and stmt[2]['statement_id'] == item[2]['statement_id']:
                    item[2]['amount'] += stmt[2]['amount']
                    found = True
                    break
            if not found:
                stmts.append(stmt)

        cash_stmts = []
        non_cash_stmts = []
        journal_obj = self.pool['account.journal']
        session = self.pool.get('pos.session').browse(cr, uid, order['pos_session_id'], context=context)
        cash_journal = session.cash_journal_id.id

        for stmt in stmts:
            journal = journal_obj.browse(cr, uid, stmt[2]['journal_id'], context=context)
            if journal.type == 'cash':
                stmt[2].update({'reason_id': journal.default_in_reason_id.id})
                cash_stmts.append(stmt)
            else:
                non_cash_stmts.append(stmt)
                cash_stmts.append([0, 0, {
                    'journal_id': cash_journal,
                    'amount': stmt[2]['amount'],
                    'name': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'statement_id': False,
                    'reason_id': journal.default_in_reason_id.id,
                }])
                cash_stmts.append([0, 0, {
                    'journal_id': cash_journal,
                    'amount': -stmt[2]['amount'],
                    'name': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'statement_id': False,
                    'reason_id': journal.default_out_reason_id.id,
                }])

        cash_stmts = sorted(cash_stmts, key=lambda x: x[2]['amount'], reverse=True)
        non_cash_stmts = sorted(non_cash_stmts, key=lambda x: x[2]['amount'], reverse=True)

        if len(cash_stmts):
            main_cash_stmt = cash_stmts[0]
            for stmt in cash_stmts:
                if stmt[2]['journal_id'] == cash_journal:
                    main_cash_stmt = stmt
                    break
        else:
            main_cash_stmt = [0, 0, {
                    'journal_id': cash_journal,
                    'amount': 0,
                    'name': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'statement_id': False,
                    'reason_id': session.cash_journal_id.default_in_reason_id.id,
                }]
            cash_stmts.append(main_cash_stmt)

        if order.get('discount_amount', False) and session.config_id.discount_reason_id:
            main_cash_stmt[2]['amount'] += order['discount_amount']
            reason = session.config_id.discount_reason_id.id
            if order['discount_pc'] == 100 and session.config_id.house_discount_reason_id:
                reason = session.config_id.house_discount_reason_id.id
            cash_stmts.append([0, 0, {
                'journal_id': cash_journal,
                'amount': -order['discount_amount'],
                'name': time.strftime('%Y-%m-%d %H:%M:%S'),
                'statement_id': main_cash_stmt[2]['statement_id'],
                'reason_id': reason,
            }])

        if order.get('tip', False) and session.config_id.tip_reason_id:
            tip_cash_statement = main_cash_stmt
            for stmt in cash_stmts:
                if stmt[2]['reason_id'] == session.cash_journal_id.default_in_reason_id.id and \
                                stmt[2]['amount'] >= order['tip']:
                    tip_cash_statement = stmt
                    break
            tip_cash_statement[2]['amount'] -= order['tip']
            cash_stmts.append([0, 0, {
                'journal_id': cash_journal,
                'amount': order['tip'],
                'name': time.strftime('%Y-%m-%d %H:%M:%S'),
                'statement_id': main_cash_stmt[2]['statement_id'],
                'reason_id': session.config_id.tip_reason_id.id,
            }])

        if order.get('service_amount', False) and session.config_id.service_fee_reason_id:
            main_cash_stmt[2]['amount'] -= order['service_amount']
            cash_stmts.append([0, 0, {
                'journal_id': cash_journal,
                'amount': order['service_amount'],
                'name': time.strftime('%Y-%m-%d %H:%M:%S'),
                'statement_id': main_cash_stmt[2]['statement_id'],
                'reason_id': session.config_id.service_fee_reason_id.id,
            }])

        order['statement_ids'] = cash_stmts + non_cash_stmts

        return order

    def _payment_fields(self, cr, uid, ui_paymentline, context=None):
        result = super(POSOrder, self)._payment_fields(cr, uid, ui_paymentline, context=context)
        result.update({'reason_id': ui_paymentline.get('reason_id', False)})
        return result

    def add_payment(self, cr, uid, order_id, data, context=None):
        """Create a new payment for the order"""
        context = dict(context or {})
        statement_line_obj = self.pool.get('account.bank.statement.line')
        property_obj = self.pool.get('ir.property')
        order = self.browse(cr, uid, order_id, context=context)
        date = data.get('payment_date', time.strftime('%Y-%m-%d'))
        if len(date) > 10:
            timestamp = datetime.strptime(date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
            ts = old_fields.datetime.context_timestamp(cr, uid, timestamp, context)
            date = ts.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
        args = {
            'amount': data['amount'],
            'reason_id': data.get('reason_id', False),
            'date': date,
            'name': order.name + ': ' + (data.get('payment_name', '') or ''),
            'partner_id': order.partner_id and self.pool.get("res.partner")._find_accounting_partner(
                order.partner_id).id or False,
        }

        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id passed to the method!"

        journal = self.pool['account.journal'].browse(cr, uid, journal_id, context=context)
        # use the company of the journal and not of the current user
        company_cxt = dict(context, force_company=journal.company_id.id)
        account_def = property_obj.get(cr, uid, 'property_account_receivable_id', 'res.partner', context=company_cxt)
        args['account_id'] = (order.partner_id and order.partner_id.property_account_receivable_id and
                              order.partner_id.property_account_receivable_id.id) or \
                             (account_def and account_def.id) or False

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make payment for the partner: "%s" (id:%d).') % (
                order.partner_id.name, order.partner_id.id,)
            raise UserError(msg)

        context.pop('pos_session_id', False)

        for statement in order.session_id.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.id
                break

        if not statement_id:
            raise UserError(_('You have to open at least one cashbox.'))

        args.update({
            'statement_id': statement_id,
            'pos_statement_id': order_id,
            'journal_id': journal_id,
            'ref': order.session_id.name,
        })

        statement_line_obj.create(cr, uid, args, context=context)

        return statement_id

    def _process_order(self, cr, uid, order, context=None):
        order = self._process_order_payments(cr, uid, order, context=context)
        return super(POSOrder, self)._process_order(cr, uid, order, context=context)