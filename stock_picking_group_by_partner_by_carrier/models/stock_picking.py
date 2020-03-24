from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_ids = fields.Many2many("sale.order", compute="_compute_sale_ids", store=True)
    # don't copy the printed state of a picking otherwise the backorder of a
    # printed picking becomes printed
    printed = fields.Boolean(copy=False)

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

    def _create_backorder(self):
        return super(
            StockPicking, self.with_context(picking_no_copy_if_can_group=1)
        )._create_backorder()

    def copy(self, defaults=None):
        if self.env.context.get("picking_no_copy_if_can_group") and self.move_lines:
            # we are in the process of the creation of a backorder. If we can
            # find a suitable picking, then use it instead of copying the one
            # we are creating a backorder from
            picking = self.move_lines[0]._search_picking_for_assignation()
            if picking:
                return picking
        return super(
            StockPicking, self.with_context(picking_no_copy_if_can_group=0)
        ).copy(defaults)
