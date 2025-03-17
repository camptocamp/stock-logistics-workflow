# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _align_group_carrier(self):
        for picking in self:
            new_group = picking.group_id.copy(
                default={"carrier_id": picking.carrier_id.id}
            )
            picking.write({"group_id": new_group.id})
            active_moves = picking.move_lines.filtered(
                lambda m: m.state not in ("done", "cancel")
            )
            active_moves.write({"group_id": new_group.id})

    def write(self, values):
        if "carrier_id" not in values:
            # We only track when carrier changes. Avoid useless computation when
            # carrier_id isn't in values
            return super().write(values)
        carrier_mapping = {record.id: record.carrier_id for record in self}
        res = super().write(values)
        # Align group on pickings where carrier was updated
        updated_pickings = self.filtered(
            lambda p: p.carrier_id != carrier_mapping.get(p.id)
        )
        updated_pickings._align_group_carrier()
        return res
