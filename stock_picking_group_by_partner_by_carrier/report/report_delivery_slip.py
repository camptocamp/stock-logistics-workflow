# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models
from odoo.tools import float_compare, float_round


class DeliverySlipReport(models.AbstractModel):
    _name = "report.stock.report_deliveryslip"
    _description = "Delivery Slip Report"

    @api.model
    def get_remaining_to_deliver_data(self, picking):
        """Return dictionaries encoding pending quantities to deliver

        Returns a list of dictionaries, encoding the data to be displayed
        at the end of the delivery slip, summarising for each order the
        pending quantities for each of its lines.
        """
        remaining_to_deliver_data = []
        report_lines = picking.get_delivery_report_lines()
        for report_line in report_lines:
            # Depending on the state of the picking, get_delivery_report_lines
            # may return move.line or stock.move.line, so we check first.
            move = (
                report_line.move_id
                if report_line._name == "stock.move.line"
                else report_line
            )

            if not report_line.id:  # Header moves are created as mock moves.
                remaining_to_deliver_data.append(
                    {"is_header": True, "concept": report_line.description_picking,}
                )
            elif (
                move.picking_id.picking_type_id.code == "outgoing" and move.sale_line_id
            ):
                sol = move.sale_line_id
                picking_state = move.picking_id.state
                qty = None
                if picking_state == "done":
                    qty = sol.product_uom._compute_quantity(
                        sol.product_uom_qty - sol.qty_delivered, move.product_uom
                    )
                elif picking_state not in {"cancel", "done"}:
                    qty = (
                        sol.product_uom._compute_quantity(
                            sol.product_uom_qty - sol.qty_delivered, move.product_uom
                        )
                        - move.product_uom_qty
                    )

                if qty:
                    remaining_to_deliver_data.append(
                        {
                            "is_header": False,
                            "concept": move.product_id.name_get()[0][-1],
                            "move": move,
                            "qty": float_round(
                                qty, precision_rounding=move.product_uom.rounding
                            ),
                        }
                    )
        return remaining_to_deliver_data

    @api.model
    def rounding_to_precision(self, rounding):
        """ Convert rounding specification to precision digits

        Rounding is encoded in Odoo as a floating number with as
        many meaningful decimals as used for the rounding, e.g.
        0.001 means rounding to 3 decimals. Precision is an integer
        that indicates that amount, directly, in this case 3. This
        method allows to convert from rounding to precision.
        """
        return len(str(int(1 / rounding))) - 1

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["stock.picking"].browse(docids)
        data = data if data is not None else {}
        docargs = {
            "doc_ids": docids,
            "doc_model": "stock.picking",
            "docs": docs,
            "get_remaining_to_deliver_data": self.get_remaining_to_deliver_data,
            "rounding_to_precision": self.rounding_to_precision,
            "data": data.get("form", False),
        }
        return docargs
