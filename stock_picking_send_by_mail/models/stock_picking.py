# Copyright 2015 - Sandra Figueroa Varela
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_picking_send_email_template(self):
        return self.company_id.stock_mail_confirmation_template_id

    def action_picking_send(self, send=False):
        """Send an e-mail from a delivery transfer.

        :param send: by default this method is opening the email composer wizard.
            If set to `True`, the email will be sent directly without confirmation.
        """
        self.ensure_one()
        template = self._get_picking_send_email_template()
        compose_form = self.env.ref(
            "mail.email_compose_message_wizard_form",
            False,
        )
        template_id = template.id if template else False
        ctx = dict(
            default_model="stock.picking",
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template_id,
            default_composition_mode="comment",
            user_id=self.env.user.id,
        )
        if send:
            # Send the email directly
            wiz = self.env["mail.compose.message"].with_context(**ctx).create({})
            values = wiz.onchange_template_id(
                template_id, "comment", self._name, self.id
            )["value"]
            wiz.write(values)
            return wiz.send_mail()
        # Open the mail composer
        return {
            "name": _("Compose Email"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }
