# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    estimated_pack_weight = fields.Float(
        help="Based on the weight of the product packagings."
    )

    @api.depends("quant_ids")
    @api.depends_context("picking_id")
    def _compute_estimated_pack_weight(self):
        # Overridden from 'stock_quant_package_dimension' module to use the
        # 'get_total_weight_from_packaging' method supplied by the
        # 'product_total_weight_from_packaging' module
        for package in self:
            weight = 0.0
            if self.env.context.get("picking_id"):
                current_picking_move_line_ids = self.env["stock.move.line"].search(
                    [
                        ("result_package_id", "=", package.id),
                        ("picking_id", "=", self.env.context["picking_id"]),
                    ]
                )
                for ml in current_picking_move_line_ids:
                    weight += ml.product_id.get_total_weight_from_packaging(ml.qty_done)
            else:
                for quant in package.quant_ids:
                    weight += quant.product_id.get_total_weight_from_packaging(
                        quant.quantity
                    )
            package.estimated_pack_weight = weight
