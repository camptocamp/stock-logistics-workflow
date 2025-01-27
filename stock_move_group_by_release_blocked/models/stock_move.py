# Copyright 2025 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _search_picking_for_assignation_domain(self):
        return super()._search_picking_for_assignation_domain() + [
            ("release_blocked", "=", self.release_blocked)
        ]
