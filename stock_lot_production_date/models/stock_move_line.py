# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _assign_production_lot(self, lot):
        super()._assign_production_lot(lot)
        if lot.product_id.use_production_date:
            lot.production_date = fields.Datetime.now()
