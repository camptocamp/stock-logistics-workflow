# -*- coding: utf-8 -*-
# © 2012-2014 Alexandre Fayolle, Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import _, api, fields, models

from openerp.exceptions import UserError


class StockBatchPicking(models.Model):
    """ This object allow to manage multiple stock.picking at the same time.
    """
    _name = 'stock.batch.picking'

    name = fields.Char(
        'Name',
        required=True, index=True,
        copy=False, unique=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'stock.batch.picking'
        ),
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Available'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')],
        string='State',
        readonly=True, index=True, copy=False,
        default='draft',
        help='the state of the batch picking. '
        'Workflow is draft -> assigned -> done or cancel'
    )

    date = fields.Date(
        'Date',
        required=True, readonly=True, index=True,
        states={
            'draft': [('readonly', False)],
            'assigned': [('readonly', False)]
        },
        default=fields.Date.context_today,
        help='date on which the batch picking is to be processed'
    )

    picker_id = fields.Many2one(
        'res.users', 'Picker',
        readonly=True, index=True,
        states={
            'draft': [('readonly', False)],
            'assigned': [('readonly', False)]
        },
        help='the user to which the pickings are assigned'
    )

    picking_ids = fields.One2many(
        'stock.picking', 'batch_picking_id', 'Pickings',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='List of picking managed by this batch.'
    )

    active_picking_ids = fields.One2many(
        'stock.picking', 'batch_picking_id', 'Pickings',
        readonly=True,
        domain=[('state', 'not in', ('cancel', 'done'))],
    )

    notes = fields.Text('Notes', help='free form remarks')

    move_ids = fields.One2many(
        'stock.move',
        readonly=True,
        string='Related stock moves',
        compute='_compute_move_ids'
    )

    pack_operation_ids = fields.One2many(
        'stock.pack.operation',
        readonly=True,
        string='Related pack operations',
        compute='_compute_pack_operation_ids'
    )

    pack_operation_product_ids = fields.One2many(
        'stock.pack.operation',
        string='Related pack operations',
        compute='_compute_pack_operation_product_ids',
        inverse=lambda *args, **kwargs: None,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )

    pack_operation_pack_ids = fields.One2many(
        'stock.pack.operation',
        string='Related pack operations',
        compute='_compute_pack_operation_pack_ids',
        inverse=lambda *args, **kwargs: None,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
    )

    @api.depends('picking_ids')
    def _compute_move_ids(self):
        for batch in self:
            batch.move_ids = batch.picking_ids.mapped("move_lines")

    @api.depends('picking_ids')
    def _compute_pack_operation_ids(self):
        for batch in self:
            batch.pack_operation_ids = batch.picking_ids.mapped(
                'pack_operation_ids'
            )

    @api.depends('picking_ids')
    def _compute_pack_operation_product_ids(self):
        for batch in self:
            batch.pack_operation_product_ids = batch.picking_ids.mapped(
                'pack_operation_product_ids'
            )

    @api.depends('picking_ids')
    def _compute_pack_operation_pack_ids(self):
        for batch in self:
            batch.pack_operation_pack_ids = batch.picking_ids.mapped(
                'pack_operation_pack_ids'
            )

    def get_not_empties(self):
        """ Retourne all batches in this recordset
        for which picking_ids is not empty.

        :raise UserError: If all batches are empty.
        """
        if not self.mapped('picking_ids'):
            if len(self) == 1:
                message = _('This Batch has no picking')
            else:
                message = _('These Batches have no picking')

            raise UserError(message)

        return self.filtered(lambda b: len(b.picking_ids) != 0)

    def verify_state(self, expected_state=None):
        """ Check if batches states must be changed based on pickings states.

        If all pickings are canceled, batch must be canceled.
        If all pickings are canceled or done, batch must be done.
        If all pickings are canceled or done or *expected_state*,
            batch must be *expected_state*.

        :return: True if batches states has been changed.
        """
        expected_states = {'done', 'cancel'}
        if expected_state is not None:
            expected_states.add(expected_state)

        all_good = True
        for batch in self.filtered(lambda b: b.state not in expected_states):
            states = set(batch.mapped('picking_ids.state'))
            if not states or states == {'cancel'}:
                batch.state = 'cancel'
            elif states == {'done'} or states == {'done', 'cancel'}:
                batch.state = 'done'

            elif states.issubset(expected_states):
                batch.state = expected_state

            else:
                all_good = False

        return all_good

    @api.multi
    def action_cancel(self):
        """ Call action_cancel for all batches pickings
        and set batches states to cancel too.
        """
        if not self.picking_ids:
            self.write({'state': 'cancel'})
        else:
            if not self.verify_state():
                self.picking_ids.action_cancel()

    @api.multi
    def action_assign(self):
        """ Check if batches pickings are available.
        """
        batches = self.get_not_empties()
        if not batches.verify_state('assigned'):
            batches.mapped('active_picking_ids').action_assign()

    @api.multi
    def action_transfer(self):
        """ Make the transfer for all active pickings in these batches
        and set state to done all picking are done.
        """
        batches = self.get_not_empties()
        for batch in batches:
            if not batch.verify_state():
                batch.active_picking_ids.force_transfer(
                    force_qties=all(
                        operation.qty_done == 0
                        for operation in batch.pack_operation_ids
                    )
                )

    @api.multi
    def remove_undone_pickings(self):
        """ Remove of this batch all pickings which state is not done / cancel.
        """
        self.mapped('active_picking_ids').write({'batch_picking_id': False})
        self.verify_state()
