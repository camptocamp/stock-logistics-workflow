# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from logging import getLogger

import pytz

from odoo import models
from odoo.osv import expression
from odoo.tools.misc import str2bool

_logger = getLogger(__name__)


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    def _get_moves_to_assign_domain(self, company_id):
        domain = super()._get_moves_to_assign_domain(company_id)
        global_limit = self.get_global_is_moves_assignation_limited()
        if global_limit:
            delay = self.get_global_moves_limit_horizon()
            domain = self._get_moves_to_assign_domain_assignation_limited(domain, delay)
        return domain

    def _get_moves_to_assign_domain_assignation_limited(self, domain, delay_days):
        applied_tz = pytz.timezone("UTC")
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
        param = "stock_scheduler_assignation_horizon.stock_horizon_move_assignation"
        return str2bool(get_param(param, False))

    def get_global_moves_limit_horizon(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        param = (
            "stock_scheduler_assignation_horizon.stock_horizon_move_assignation_limit"
        )
        try:
            param_value = get_param(param, 0)
            limit = int(param_value)
        except ValueError:
            limit = 0
            _logger.warning(
                "Wrong value for ir.config_parameter %s: %s . Using %s as default value"
                % (param, param_value, limit)
            )
        return limit
