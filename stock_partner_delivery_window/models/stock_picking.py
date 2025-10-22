# Copyright 2020 Camptocamp SA
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from datetime import date, datetime

from odoo import api, fields, models
from odoo.tools.misc import format_datetime


class StockPicking(models.Model):
    _inherit = "stock.picking"
    partner_delivery_window_warning = fields.Text(
        compute="_compute_partner_delivery_window_warning"
    )

    def _planned_delivery_date(self):
        return self.scheduled_date

    @api.depends("partner_id", "scheduled_date")
    def _compute_partner_delivery_window_warning(self):
        for picking in self:
            partner = picking.partner_id
            picking.partner_delivery_window_warning = False
            if not partner:
                continue

            anytime_delivery = partner and partner.delivery_time_preference == "anytime"
            not_outgoing_picking = picking.picking_type_id.code != "outgoing"

            delivery_date = picking._planned_delivery_date()

            if anytime_delivery or not_outgoing_picking:
                continue

            elif not delivery_date:
                picking.partner_delivery_window_warning = self.env._(
                    "No scheduled delivery date is set on the picking, cannot check "
                    "if it is in partner's delivery window."
                )

            elif not partner.is_in_delivery_window(delivery_date):
                picking.partner_delivery_window_warning = (
                    picking._scheduled_date_no_delivery_window_match_msg()
                )

    def _scheduled_date_no_delivery_window_match_msg(self):
        delivery_date = self._planned_delivery_date()
        if isinstance(delivery_date, date):
            delivery_date = datetime.combine(delivery_date, datetime.min.time())
        formatted_delivery_date = format_datetime(self.env, delivery_date)
        name_delivery_date = (
            "scheduled date"
            if delivery_date == self.scheduled_date
            else "delivery date"
        )
        partner = self.partner_id
        if partner.delivery_time_preference == "workdays":
            message = self.env._(
                "The %(date_name)s is %(date)s %(weekday)s, but the partner is "
                "set to prefer deliveries on working days.",
                date_name=name_delivery_date,
                date=formatted_delivery_date,
                weekday=delivery_date.weekday(),
            )
        else:
            delivery_windows_strings = []
            if partner:
                for w in partner.get_delivery_windows().get(partner.id):
                    delivery_windows_strings.append(
                        f"  * {w.display_name} ({partner.tz})"
                    )
            message = self.env._(
                "The %(date_name)s is %(date)s (%(tz)s), but the partner is "
                "set to prefer deliveries on following time windows:\n%(window)s",
                date_name=name_delivery_date,
                date=format_datetime(self.env, delivery_date),
                tz=self.env.context.get("tz"),
                window="\n".join(delivery_windows_strings),
            )
        return message
