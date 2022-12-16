# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    use_production_date = fields.Boolean(
        string="Use Production Date", related="product_id.use_production_date")
    production_date = fields.Datetime(
        help="This is the date when the goods with this lot/serial number have been produced.")
