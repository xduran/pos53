# -*- coding: utf-8 -*-

import logging

import openerp
from openerp import api, tools, fields, models, _


_logger = logging.getLogger(__name__)


class POSWorkOrderStage(models.Model):
    _name = 'pos.work.order.stage'
    _description = "Stage of work order"
    _rec_name = 'name'
    _order = "sequence"

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=1, help="Used to order stages.")
    fold = fields.Boolean(string='Folded in Pipeline', default=False, help='This stage is folded in the kanban view.')
    next_stage = fields.Many2one('pos.work.order.stage', string='Next', compute='compute_previous_and_next_stages')
    previous_stage = fields.Many2one('pos.work.order.stage', string='Previous',
                                     compute='compute_previous_and_next_stages')

    @api.multi
    def compute_previous_and_next_stages(self):
        for stage in self:
            next_stages = self.search([('id', '!=', stage.id), ('sequence', '>=', stage.sequence)])
            previous_stages = self.search([('id', '!=', stage.id), ('sequence', '<=', stage.sequence)])
            if len(next_stages):
                stage.next_stage = next_stages[0]
            else:
                stage.next_stage = False
            if len(previous_stages):
                stage.previous_stage = previous_stages[-1]
            else:
                stage.previous_stage = False


class POSWorkOrder(models.Model):
    _name = 'pos.work.order'
    _description = 'Work order'
    _rec_name = 'product_id'
    _order = 'create_date, table_id'

    session_id = fields.Many2one('pos.session', string='Session', required=True, select=1, readonly=True)
    config_id = fields.Many2one(related='session_id.config_id')
    table_id = fields.Many2one('restaurant.table', string='Table')
    waiter_id = fields.Many2one('pos.waiter', string='Waiter')
    order = fields.Char(string='Order', compute='_fields_compute', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    pos_categ_id = fields.Many2one(related='product_id.pos_categ_id')
    quantity = fields.Integer(string='Quantity', default=1)
    name = fields.Char(string='Name', compute='_fields_compute', readonly=True)
    note = fields.Text(string='Note')
    stage_id = fields.Many2one('pos.work.order.stage', string='Stage', track_visibility='onchange', select=True,
                               default=lambda self: self._default_stage())
    garnish_ids = fields.One2many('pos.work.order.garnish', 'work_order_id', string='Order garnish',
                                  help="Selected garnish for the order.")
    garnish_text = fields.Char(string='Garnish', compute='_garnish_text_compute', readonly=True)
    # color = fields.Integer(string='Color Index', default=0, readonly=True),
    create_date = fields.Datetime(string="Creation Date", readonly=True, select=True)
    write_date = fields.Datetime(string="Update Date", readonly=True)

    @api.multi
    def _fields_compute(self):
        for work_order in self:
            work_order.order = work_order.table_id.floor_id.name + '-' + work_order.table_id.name
            work_order.name = "%d - %s" % (work_order.quantity, work_order.product_id.name)

    @api.multi
    def _garnish_text_compute(self):
        for work_order in self:
            garnish_text = ""
            garnish_names = [g.garnish_id.name for g in work_order.garnish_ids]
            if garnish_names:
                garnish_text = "(" + ', '.join(garnish_names) + ")"
            work_order.garnish_text = garnish_text

    def _default_stage(self):
        return self.env.ref('pos_restaurant_work_orders.pos_work_order_stage_1')

    def _read_group_stage_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        if context is None:
            context = {}
        access_rights_uid = access_rights_uid or uid
        stage_obj = self.pool.get('pos.work.order.stage')
        order = stage_obj._order
        # lame hack to allow reverting search, should just work in the trivial case
        if read_group_order == 'stage_id desc':
            order = "%s desc" % order

        search_domain = []
        # perform search
        stage_ids = stage_obj._search(cr, uid, search_domain, order=order, access_rights_uid=access_rights_uid,
                                      context=context)
        result = stage_obj.name_get(cr, access_rights_uid, stage_ids, context=context)
        # restore order of the search
        result.sort(lambda x, y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))

        fold = {}
        for stage in stage_obj.browse(cr, access_rights_uid, stage_ids, context=context):
            fold[stage.id] = stage.fold or False
        return result, fold

    _group_by_full = {
        'stage_id': _read_group_stage_ids
    }

    def create_from_ui(self, cr, uid, orders, context=None):
        """ create or modify a work order from the point of sale ui."""
        result = {}
        garnish_line_obj = self.pool.get('pos.work.order.garnish')
        for order in orders:
            order_id = False
            garnish_ids = []
            if order.get('garnish_ids', False):
                garnish_ids = order['garnish_ids']
                del order['garnish_ids']
            if order.get('id', False):
                order_id = order['id']
                del order['id']
            hash_str = order['hash_str']
            del order['hash_str']

            if order_id:
                self.write(cr, uid, order_id, order, context=context)
                if garnish_ids:
                    garnish_lines = garnish_line_obj.search(cr, uid, [('work_order_id', '=', order_id)],
                                                            context=context)
                    garnish_line_obj.unlink(cr, uid, garnish_lines, context=context)
            else:
                order_id = self.create(cr, uid, order, context=context)
            if garnish_ids:
                for garnish_id in garnish_ids:
                    values = {
                        'work_order_id': order_id,
                        'garnish_id': garnish_id,
                    }
                    self.pool.get('pos.work.order.garnish').create(cr, uid, values, context=context)
            stage_id = self.browse(cr, uid, order_id, context=context).stage_id.id
            result[hash_str] = order_id, stage_id
        return result

    def get_stage_from_ui(self, cr, uid, ids, context=None):
        if not isinstance(ids, list):
            ids = [ids]
        result = {}
        orders = self.read(cr, uid, ids, ['stage_id'], context=context)
        for order in orders:
            result[order['id']] = order['stage_id'][0]
        return result

    @api.multi
    def action_workflow_move_forward(self):
        for work_order in self:
            if work_order.stage_id.next_stage:
                work_order.stage_id = work_order.stage_id.next_stage.id

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_workflow_move_backward(self):
        for work_order in self:
            if work_order.stage_id.previous_stage:
                work_order.stage_id = work_order.stage_id.previous_stage.id
        return {'type': 'ir.actions.act_window_close'}


class PosWorkOrderGarnish(models.Model):
    _name = 'pos.work.order.garnish'

    work_order_id = fields.Many2one('pos.work.order', string='Order', ondelete='cascade')
    garnish_id = fields.Many2one('product.garnish', string='Garnish', required=True)


class POSSession(models.Model):
    _inherit = 'pos.session'

    work_order_ids = fields.One2many('pos.work.order', 'session_id', string='Work Orders',
                                     help="Work orders of this session.")
    work_order_count = fields.Integer(compute='_work_order_count', string="Work Orders")

    @api.multi
    def _work_order_count(self):
        for session in self:
            session.work_order_count = self.env['pos.work.order'].search_count([('session_id', '=', session.id)])


class POSCategory(models.Model):
    _inherit = 'pos.category'
    _parent_store = True

    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)

    @api.multi
    def action_work_orders(self):
        ctx = self._context.copy()
        model = 'pos.work.order'

        view_id = self.env.ref('pos_restaurant_work_orders.pos_work_order_kanban_view').id
        domain = "[('session_id.state','=','opened'), ('pos_categ_id','child_of', %d)]" % self.id

        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'kanban',
            'res_model': model,
            'auto_refresh': 10,
            'view_id': view_id,
            'domain': domain,
            'context': ctx,
        }
