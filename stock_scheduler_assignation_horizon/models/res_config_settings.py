# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    global_moves_assignation = fields.Boolean(
        "Use global Assignation Limit",
        config_parameter="s_scheduler_assignation_horizon.global_moves_assignation",
        readonly=False,
        help="Check this box to allow limit settings " "for each company independent",
    )
    global_moves_assignation_horizon = fields.Integer(
        "Assignation Horizon",
        config_parameter="s_scheduler_assignation_horizon.stock_scheduler_assignation_horizon",
        readonly=False,
        help="Only reserve moves that are scheduled within the specified number of days",
    )
    is_moves_assignation_limited = fields.Boolean(
        "Scheduler Assignation Limit",
        related="company_id.is_moves_assignation_limited",
        readonly=False,
        help="Check this box to prevent the scheduler from "
        "assigning moves before the horizon below",
    )
    moves_assignation_horizon = fields.Integer(
        "Assignation Horizon",
        related="company_id.moves_assignation_horizon",
        readonly=False,
        help="Only reserve moves that are scheduled within the specified number of days",
    )

    @api.constrains("moves_assignation_horizon")
    def _check_moves_assignation_horizon(self):
        for record in self:
            if record.moves_assignation_horizon < 0:
                raise ValidationError(_("The assignation horizon cannot be negative"))

    def get_global_is_moves_assignation_limited(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        param = "s_scheduler_assignation_horizon.global_moves_assignation"
        return safe_eval(get_param(param, False))

    def get_global_moves_limit_horizon(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        param = "s_scheduler_assignation_horizon.stock_scheduler_assignation_horizon"
        return safe_eval(get_param(param, 0))
