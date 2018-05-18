# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields


class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    orig_procurement_qty = fields.Float()

    @api.multi
    def _create_stock_moves(self, picking):
        """ When creating the moves from a PO, propagate the procurement group
            and quantity from the PO lines to the destination moves, and
            reassign pickings.
        """
        moves = super(PurchaseOrderLine, self)._create_stock_moves(picking)
        destination_moves_to_prop = moves.get_next_moves_to_propagate()
        destination_moves_to_prop._propagate_procurement_group(
            moves.mapped('group_id'))
        for move in moves:
            move._propagate_quantity_to_dest_moves(
                move.purchase_line_id.orig_procurement_qty,
                move.purchase_line_id.product_uom
            )
        return moves
