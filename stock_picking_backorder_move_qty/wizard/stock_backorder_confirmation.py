# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class StockBackorderConfirmation(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    backorder_confirmation_move_line_ids = fields.One2many(
        "stock.backorder.confirmation.move.line",
        "backorder_confirmation_id",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if "backorder_confirmation_move_line_ids" in fields and res.get("pick_ids"):
            # default_get returns x2m values as [(6, 0, ids)]
            # because of webclient limitations
            pickings = self.env["stock.picking"].browse(res["pick_ids"][0][2])

            res["backorder_confirmation_move_line_ids"] = [
                (0, 0, {"move_id": move.id}) for move in pickings.move_ids
            ]

        return res

    def process(self):
        prec = self.env["decimal.precision"].precision_get("Product Unit")
        if not self.show_transfers and (
            any(
                float_compare(
                    wiz_line.qty_unprocessed,
                    wiz_line.qty_to_backorder,
                    precision_digits=prec,
                )
                != 0
                for wiz_line in self.backorder_confirmation_move_line_ids
            )
            or len(self.backorder_confirmation_move_line_ids)
            != len(self.pick_ids.move_ids)
        ):
            moves_qty_to_backorder = {
                wiz_line.move_id.id: wiz_line.qty_to_backorder
                for wiz_line in self.backorder_confirmation_move_line_ids
            }
            self = self.with_context(
                force_moves_qty_to_backorder=moves_qty_to_backorder
            )
        return super().process()


class StockBackorderConfirmationMove(models.TransientModel):
    _name = "stock.backorder.confirmation.move.line"
    _description = "Backorder Confirmation Move Line"

    backorder_confirmation_id = fields.Many2one(
        "stock.backorder.confirmation", "Immediate Transfer"
    )
    picking_id = fields.Many2one("stock.picking", related="move_id.picking_id")
    move_id = fields.Many2one("stock.move", "Move")
    qty_unprocessed = fields.Float(compute="_compute_qty_unprocessed")
    qty_to_backorder = fields.Float(
        compute="_compute_qty_to_backorder", store=True, readonly=False
    )
    qty_to_backorder_uom_id = fields.Many2one("uom.uom", related="move_id.product_uom")

    @api.depends(
        "move_id",
        "move_id.picked",
        "move_id.product_uom",
        "move_id.product_uom_qty",
        "move_id.quantity",
        "move_id.state",
        "move_id.move_line_ids.picked"
        "move_id.move_line_ids.product_uom_id"
        "move_id.move_line_ids.quantity",
    )
    def _compute_qty_unprocessed(self):
        for line in self:
            move = line.move_id
            if move.state != "cancel":
                unprocessed = (
                    move.product_uom_qty
                    if not move.picked
                    else move.product_uom_qty - move._get_picked_quantity()
                )
            else:
                unprocessed = 0
            line.qty_unprocessed = unprocessed

    @api.depends("qty_unprocessed")
    def _compute_qty_to_backorder(self):
        for line in self:
            line.qty_to_backorder = line.qty_unprocessed

    @api.constrains("qty_to_backorder")
    def _check_qty_to_backorder(self):
        prec = self.env["decimal.precision"].precision_get("Product Unit")
        for line in self:
            msg = False
            if float_compare(line.qty_to_backorder, 0, precision_digits=prec) < 0:
                msg = self.env._("Quantity to backorder cannot be negative")
            if (
                float_compare(
                    line.qty_to_backorder, line.qty_unprocessed, precision_digits=prec
                )
                > 0
            ):
                msg = self.env._(
                    "Quantity to backorder cannot exceed the remaining unprocessed "
                    "quantity"
                )
            if msg:
                raise ValidationError(msg)
