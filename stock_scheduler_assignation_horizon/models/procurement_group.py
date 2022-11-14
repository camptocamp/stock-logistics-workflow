# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

import pytz

from odoo import models
from odoo.osv import expression


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    def _get_moves_to_assign_domain(self, company_id):
        domain = super()._get_moves_to_assign_domain(company_id)
        company = self.env["res.company"].browse(company_id)
        settings = self.env["res.config.settings"]
        global_limit = settings.get_global_is_moves_assignation_limited()
        if company.is_moves_assignation_limited or global_limit:
            delay = (
                company.moves_assignation_horizon
                or settings.get_global_moves_limit_horizon()
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
