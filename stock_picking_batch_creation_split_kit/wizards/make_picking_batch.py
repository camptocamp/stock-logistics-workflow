# Copyright 2025 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MakePickingBatch(models.TransientModel):
    _inherit = "make.picking.batch"

    def _get_picking_kit_quantity(self, picking):
        """Compute the kit quantity of the picking

        The kit quantity is the number of kits + number of regular products
        in the picking.
        """
        kit_moves = picking.move_ids.filtered(
            lambda m: m.bom_line_id.bom_id.type == "phantom"
        )
        kit_moves_by_bom = kit_moves.grouped(lambda m: m.bom_line_id.bom_id)
        kit_quantity = 0.0
        # Process kits
        for bom, moves in kit_moves_by_bom.items():
            kit_quantity += moves._compute_kit_quantities(
                bom.product_id,
                max(moves.mapped("product_qty")),
                bom,
                {
                    "incoming_moves": lambda m: True,
                    "outgoing_moves": lambda m: False,
                },
            )
        # Process regular products
        regular_moves = picking.move_ids - kit_moves
        kit_quantity += sum(regular_moves.mapped("product_uom_qty"))
        return kit_quantity

    def _is_picking_exceeding_kit_quantity_limits(self, picking):
        last_device = self.stock_device_type_ids[-1]
        if not last_device.nbr_bins:
            return False
        kit_quantity = self._get_picking_kit_quantity(picking)
        return kit_quantity > last_device.nbr_bins

    def _is_picking_exceeding_limits(self, picking):
        # OVERRIDE to check also the nbr_bins and the kit quantity
        return super()._is_picking_exceeding_limits(
            picking
        ) or self._is_picking_exceeding_kit_quantity_limits(picking)

    def _split_first_picking_for_limit(self, picking):
        # OVERRIDE to handle kit quantity mode
        if self._is_picking_exceeding_kit_quantity_limits(picking):
            last_device = self.stock_device_type_ids[-1]
            max_nbr_bins = last_device.nbr_bins
            picking = (
                self.env["stock.split.picking"]
                .with_context(active_ids=picking.ids)
                .create(
                    {
                        "mode": "kit_quantity",
                        "kit_split_quantity": max_nbr_bins,
                    }
                )
                ._action_apply()
            )
            # At this stage, check again if the picking is exceeding the dimensions
            if self._is_picking_exceeding_limits(picking):
                return super()._split_first_picking_for_limit(picking)
            return picking
        # Otherwise, fallback to original behavior
        return super()._split_first_picking_for_limit(picking)
