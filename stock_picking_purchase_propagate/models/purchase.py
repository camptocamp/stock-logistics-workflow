# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    @api.multi
    def _create_stock_moves(self, picking):
        """ When creating the moves from a PO, propagate the procurement group
            and quantity from the PO lines to the destination moves, and
            reassign pickings.
        """
        moves = super(PurchaseOrderLine, self)._create_stock_moves(picking)

        sql = """
            SELECT dest_mov.id
            FROM stock_move dest_mov
            INNER JOIN stock_move_move_rel rel
                ON rel.move_dest_id = dest_mov.id
            INNER JOIN stock_move orig_mov ON rel.move_orig_id = orig_mov.id
            WHERE orig_mov.propagate = TRUE
            AND dest_mov.group_id IS NULL
            AND orig_mov.id IN %s;
            """
        self.env.cr.execute(sql, [tuple(moves.ids)])
        dest_moves_ids = [x[0] for x in self.env.cr.fetchall()]
        destination_moves_to_prop = self.env['stock.move'].browse(
            dest_moves_ids)

        destination_moves_to_prop._propagate_procurement_group(
            moves.mapped('group_id'))
        moves._propagate_quantity_to_dest_moves()
        return moves

    def _merge_in_existing_line(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        """ This function purpose is to be override with the purpose to forbide _run_buy  method
        to merge a new po line in an existing one.
        """
        # TODO Do not merge if coming from different procurement group
        # Cf purchase.py line 922-932
        pass
