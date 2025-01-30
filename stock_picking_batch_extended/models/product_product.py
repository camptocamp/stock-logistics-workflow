# Copyright 2012-2014 Alexandre Fayolle, Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    description_picking = fields.Text(string="Warehouse Description", translate=True)
