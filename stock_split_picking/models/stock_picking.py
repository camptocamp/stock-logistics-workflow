# Copyright 2013-2015 Camptocamp SA - Nicolas Bessi
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    """Adds picking split without done state."""

    _inherit = "stock.picking"

    @api.multi
    def split_process(self):
        """Use to trigger the wizard from button with correct context"""
        for picking in self:

            # Check the picking state and condition before split
            if picking.state == 'draft':
                raise UserError(_('Mark as todo this picking please.'))
            if all([x.qty_done == 0.0 for x in picking.move_line_ids]):
                raise UserError(
                    _('You must enter done quantity in order to split your '
                      'picking in several ones.'))

            # Split moves where necessary and move quants
            moves_to_move = self.env['stock.move']
            for move in picking.move_lines:
                rounding = move.product_uom.rounding
                if float_compare(move.quantity_done, move.product_uom_qty,
                                 precision_rounding=rounding) < 0:
                    # Need to do some kind of conversion here
                    qty_split = move.product_uom._compute_quantity(
                        move.product_uom_qty - move.quantity_done,
                        move.product_id.uom_id, rounding_method='HALF-UP')
                    new_move_id = move._split(qty_split)
                    for move_line in move.move_line_ids:
                        if move_line.product_qty and move_line.qty_done:
                            # FIXME: there will be an issue
                            # if the move was partially available
                            # By decreasing `product_qty`,
                            # we free the reservation.
                            # FIXME: if qty_done > product_qty,
                            # this could raise if nothing is in stock
                            try:
                                move_line.write(
                                    {'product_uom_qty': move_line.qty_done})
                            except UserError:
                                pass

                    moves_to_move |= self.env['stock.move'].browse(new_move_id)

            # If we have moves to move, create the backorder picking
            if moves_to_move:
                backorder_picking = picking.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [],
                    'backorder_id': picking.id
                })
                picking.message_post(_(
                    'The backorder <a href=# data-oe-model='
                    'stock.picking data-oe-id=%d>%s</a> has been created.') % (
                                     backorder_picking.id,
                                     backorder_picking.name))
                moves_to_move.write(
                    {'picking_id': backorder_picking.id})
                moves_to_move.mapped('move_line_ids').write(
                    {'picking_id': backorder_picking.id})
                moves_to_move._action_assign()
