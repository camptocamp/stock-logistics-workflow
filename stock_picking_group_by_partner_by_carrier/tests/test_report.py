# Copyright 2021 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import TestGroupByBase


class TestReport(TestGroupByBase):
    def test_delivery_report_lines_two_sales_merged(self):
        """Check report lines for two sale orders merged in same picking."""
        so1 = self._get_new_sale_order()
        so2 = self._get_new_sale_order(amount=11)
        so1.action_confirm()
        so2.action_confirm()
        picking = so1.picking_ids
        res = picking.get_delivery_report_lines()
        self.assertEqual(len(res), 4)
        self.assertEqual(res._name, "stock.move")
        # Check that we have two fake moves (header with sale name)
        # And two real moves.
        self.assertTrue(res[0].is_fake)
        self.assertFalse(res[1].is_fake)
        self.assertTrue(res[2].is_fake)
        self.assertFalse(res[3].is_fake)
        # Deliver and test again
        self._update_qty_in_location(
            picking.location_id,
            so1.order_line[0].product_id,
            so1.order_line[0].product_uom_qty,
        )
        self._update_qty_in_location(
            picking.location_id,
            so2.order_line[0].product_id,
            so2.order_line[0].product_uom_qty,
        )
        picking.action_assign()
        line = picking.move_lines[0].move_line_ids
        line.qty_done = line.product_uom_qty
        line = picking.move_lines[1].move_line_ids
        line.qty_done = line.product_uom_qty
        res = picking.action_done()
        self.assertEqual(picking.state, "done")
        res = picking.get_delivery_report_lines()
        self.assertEqual(len(res), 4)
        self.assertEqual(res._name, "stock.move.line")
        # Check that we have two fake move lines (header with sale name)
        # And two real move lines.
        self.assertTrue(res[0].is_fake)
        self.assertFalse(res[1].is_fake)
        self.assertTrue(res[2].is_fake)
        self.assertFalse(res[3].is_fake)
