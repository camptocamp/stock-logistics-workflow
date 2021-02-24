# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from collections import OrderedDict

from odoo import api, models
from odoo.tools import float_is_zero, float_round


class DeliverySlipReport(models.AbstractModel):
    _name = "report.stock.report_deliveryslip"
    _description = "Delivery Slip Report"

    @api.model
    def _get_move_and_order(self, report_line):
        """Return the move and sale order associated to the report line

        Depending on the state of the picking, get_delivery_report_lines,
        the method that overwrites the report lines in this module, that
        we receive as a parameter, may return stock.move or
        stock.move.line, so we check first.
        """
        move = (
            report_line.move_id
            if report_line._name == "stock.move.line"
            else report_line
        )
        if not report_line.id:
            sale = self.env["sale.order"].search(
                [("name", "=", report_line.origin)], limit=1
            )
        else:
            sale = move.sale_line_id.order_id
        return move, sale

    @api.model
    def get_remaining_to_deliver_data(self, picking, report_lines):
        """Return dictionaries encoding pending quantities to deliver

        Returns a list of dictionaries, encoding the data to be displayed
        at the end of the delivery slip, summarising for each order the
        pending quantities for each of its lines.
        """
        sos_data = OrderedDict()
        last_sale_order_name = None
        for report_line in report_lines:
            move, sale = self._get_move_and_order(report_line)

            if not report_line.id:  # Header moves are created as mock moves.
                sos_data[sale.name] = [
                    {"is_header": True, "concept": report_line.description_picking}
                ]
                last_sale_order_name = sale.name

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

                uom_precision_rounding = move.product_uom.rounding
                if not float_is_zero(qty, precision_rounding=uom_precision_rounding):
                    if last_sale_order_name is None:
                        # We are in the special case in which there is only one
                        # sale order. In that case, no header line is introduced,
                        # so the last sale order line is not yet set. We set it
                        # here. Since there is no header, the report_line has no
                        # field description_picking set, so we have to
                        last_sale_order_name = report_line.origin
                        sos_data[last_sale_order_name] = [
                            {
                                "is_header": True,
                                "concept": sale.get_name_for_delivery_line(),
                            }
                        ]
                    sos_data[last_sale_order_name].append(
                        {
                            "is_header": False,
                            "concept": move.product_id.name_get()[0][-1],
                            "move": move,
                            "qty": float_round(
                                qty, precision_rounding=uom_precision_rounding
                            ),
                            "product": move.product_id,
                            "uom": move.product_uom,
                        }
                    )

        # Maybe some sale orders had lines that were not delivered at all.
        # We show them also as quantities that are pending to be delivered.
        if picking.state == "done":
            for sale in picking.group_id.sale_ids:
                for sale_line in sale.order_line:
                    uom_precision_rounding = sale_line.product_id.uom_id.rounding
                    if float_is_zero(
                        sale_line.qty_delivered,
                        precision_rounding=uom_precision_rounding,
                    ):
                        if sale.name not in sos_data:
                            sos_data[sale.name] = [
                                {
                                    "is_header": True,
                                    "concept": sale.get_name_for_delivery_line(),
                                }
                            ]
                        sos_data.setdefault(sale.name, []).append(
                            {
                                "is_header": False,
                                "concept": sale_line.product_id.name_get()[0][-1],
                                "qty": float_round(
                                    sale_line.product_uom_qty,
                                    precision_rounding=uom_precision_rounding,
                                ),
                                "product": sale_line.product_id,
                                "uom": sale_line.product_id.uom_id,
                            }
                        )

        # Filters out SOs that have nothing pending to be delivered.
        remaining_to_deliver_data = []
        for _, so_data in sos_data.items():
            if len(so_data) > 1:
                remaining_to_deliver_data.extend(so_data)
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
