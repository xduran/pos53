
from openerp import models, fields, api, _
from openerp.exceptions import UserError

from openerp.addons.account.wizard.pos_box import CashBox


class PosBox(CashBox):
    _register = False

    name = fields.Many2one('cash.box.reason', string='Reason', required=True)
    note = fields.Text(string='Notes')


class PosBoxIn(PosBox):
    _inherit = 'cash.box.in'
    
    @api.one
    def _calculate_values_for_statement_line(self, record):
        result = super(PosBoxIn, self)._calculate_values_for_statement_line(record)[0]
        result['reason_id'] = self.name.id
        result['name'] = self.name.name
        result['note'] = self.note
        return result

  
class PosBoxOut(PosBox):
    _inherit = 'cash.box.out'
    
    @api.one
    def _calculate_values_for_statement_line(self, record):
        result = super(PosBoxOut, self)._calculate_values_for_statement_line(record)[0]
        result['reason_id'] = self.name.id
        result['name'] = self.name.name
        result['note'] = self.note
        return result
