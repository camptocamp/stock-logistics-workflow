# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from collections import defaultdict

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_picked_quantity(self):
        if self._ml_has_qty_picked():
            return self._sum_ml_qty_picked()
        return super()._get_picked_quantity()

    @api.depends("move_line_ids.picked", "move_line_ids.qty_picked")
    def _compute_quantity(self):
        picked_moves_ids = []
        for move in self:
            if move.picked and any(ml.qty_picked for ml in move.move_line_ids):
                picked_moves_ids.append(move.id)
        picked_moves_ids = self.browse(picked_moves_ids)

        # Copied from odoo and adapted for qty_picked
        data = self.env["stock.move.line"]._read_group(
            [("id", "in", picked_moves_ids.move_line_ids.ids)],
            ["move_id", "product_uom_id"],
            ["qty_picked:sum"],
        )
        sum_qty = defaultdict(float)
        for move, product_uom, qty_sum in data:
            uom = move.product_uom
            sum_qty[move.id] += product_uom._compute_quantity(qty_sum, uom, round=False)

        for move in picked_moves_ids:
            move.quantity = sum_qty[move.id]

        not_picked_moves = self - picked_moves_ids
        return super(StockMove, not_picked_moves)._compute_quantity()

    def _quantity_sml(self):
        if self._ml_has_qty_picked():
            return self._sum_ml_qty_picked()
        return super()._quantity_sml()

    def _ml_has_qty_picked(self):
        self.ensure_one()
        return self.picked and any(ml.qty_picked for ml in self.move_line_ids)

    def _sum_ml_qty_picked(self):
        self.ensure_one()
        quantity = 0
        for move_line in self.move_line_ids:
            quantity += move_line.product_uom_id._compute_quantity(
                move_line.qty_picked, self.product_uom, round=False
            )
        return quantity

    def _action_done(self, cancel_backorder=False):
        # Override to ensure 'product_uom_qty' aligns with the picked qty
        # (especially with partial picked qty) when backorder is cancelled.
        # Context: Odoo 18 expects to pick all reserved qty when we validate
        # a move/transfer, which is not what we want anymore with the new
        # 'qty_picked' field on 'stock.move.line'.
        # Field 'product_uom_qty' is updated at only one place: when the move is
        # split, like during the creation of a backorder move.
        if cancel_backorder:
            for move in self:
                if move.state not in ("assigned", "partially_available"):
                    continue
                move.product_uom_qty = move.quantity
        return super()._action_done(cancel_backorder=cancel_backorder)
