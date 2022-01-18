# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

_logger = logging.getLogger(__name__)

try:
    from openupgradelib import openupgrade
except ImportError as err:
    _logger.debug(err)


def migrate(cr, version):
    """Extract feature to this module"""
    openupgrade.update_module_moved_fields(
        cr,
        "procurement.group",
        ["carrier_id"],
        "stock_picking_group_by_partner_by_carrier",
        "delivery_procurement_group_carrier",
    )
