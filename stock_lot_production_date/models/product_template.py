# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    use_production_date = fields.Boolean(
        string="Production Date",
        help=(
            "When this box is ticked, the date of production "
            "will be set automatically on lot/serial numbers."
        )
    )
