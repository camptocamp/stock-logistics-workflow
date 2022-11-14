# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

import pytz

from odoo import models
from odoo.osv import expression
from odoo.tools.misc import str2bool
from odoo.tools.safe_eval import safe_eval


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    def _get_moves_to_assign_domain(self, company_id):
        domain = super()._get_moves_to_assign_domain(company_id)
        company = self.env["res.company"].browse(company_id)
        global_limit = self.get_global_is_moves_assignation_limited()
        if company.is_moves_assignation_limited or global_limit:
            delay = (
                company.moves_assignation_horizon
                or self.get_global_moves_limit_horizon()
            )
            domain = self._get_moves_to_assign_domain_assignation_limited(
                domain, company.partner_id.tz, delay
            )
        return domain

    def _get_moves_to_assign_domain_assignation_limited(self, domain, tz, delay_days):
        applied_tz = pytz.timezone(tz or "UTC")
        max_date = (
            datetime.combine(
                datetime.now(applied_tz) + timedelta(days=delay_days),
                datetime.max.time(),
            )
            .astimezone(pytz.utc)
            .replace(tzinfo=None)
        )
        return expression.AND(
            [
                domain,
                [("date", "<=", max_date)],
            ]
        )

    def get_global_is_moves_assignation_limited(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        param = "s_scheduler_assignation_horizon.stock_horizon_move_assignation"
        return str2bool(get_param(param, False))

    def get_global_moves_limit_horizon(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        param = "s_scheduler_assignation_horizon.stock_horizon_move_assignation_limit"
        return safe_eval(get_param(param, 0))
