# Copyright 2024 Camptocamp (<https://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    note = fields.Html(compute="_compute_note", store=True)

    @api.depends("partner_id")
    def _compute_note(self):
        for picking in self:
            pickig_type_note_type_ids = picking.mapped(
                "picking_type_id.partner_note_type_ids"
            )
            partner_picking_note_ids = picking.mapped(
                "partner_id.stock_picking_note_ids"
            )
            picking_notes = []

            for note in partner_picking_note_ids:
                if note.note_type_id in pickig_type_note_type_ids:
                    picking_notes += [note.name]
            picking.note = "<br>".join(picking_notes)
