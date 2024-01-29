# Copyright 2024 Camptocamp (<https://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class StockPickingNote(models.Model):
    _name = "stock.picking.note"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    note_type_id = fields.Many2one("stock.picking.note.type", required=True)
