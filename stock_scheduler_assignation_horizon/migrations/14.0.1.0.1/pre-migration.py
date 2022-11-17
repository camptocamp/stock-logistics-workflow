# Copyright 2022 Camtocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api
from odoo.tools.sql import column_exists


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if column_exists(cr, "res_company", "is_moves_assignation_limited"):
        query = " SELECT is_moves_assignation_limited FROM res_company"
        cr.execute(query)
        res = cr.fetchone()

        create_param = [x for x in res if x is True]
        if create_param:
            env["ir.config_parameter"].sudo().set_param(
                "stock_scheduler_assignation_horizon.stock_horizon_move_assignation",
                True,
            )
            query = " SELECT stock_horizon_move_assignation_limit FROM res_company"
            cr.execute(query)
            res = cr.fetchone()
            limit = [x for x in res if x is True]
            if limit:
                env["ir.config_parameter"].sudo().set_param(
                    "stock_scheduler_assignation_horizon.stock_horizon_move_assignation_limit",
                    limit[0],
                )
