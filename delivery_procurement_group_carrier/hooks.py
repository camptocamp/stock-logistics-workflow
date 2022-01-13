# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from openupgradelib import openupgrade


def migrate(cr):
    """Extract feature to this module"""
    openupgrade.update_module_moved_fields(
        cr,
        "procurement.group",
        ["carrier_id"],
        "stock_picking_group_by_partner_by_carrier",
        "delivery_procurement_group_carrier",
    )
