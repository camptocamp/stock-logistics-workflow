from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_ids = fields.Many2many("sale.order", compute="_compute_sale_ids", store=True)

    @api.depends("move_lines.sale_line_id.order_id")
    def _compute_sale_ids(self):
        for rec in self:
            rec.sale_ids = rec.mapped("move_lines.sale_line_id.order_id")

    def write(self, values):
        if self.env.context.get("picking_no_overwrite_partner_origin"):
            written_fields = set(values.keys())
            if written_fields == {"partner_id", "origin"}:
                values = {}
        return super().write(values)
