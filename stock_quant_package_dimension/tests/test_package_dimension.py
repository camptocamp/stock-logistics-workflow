# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.tests import SavepointCase, Form


class TestStockQuantPackageProductPackaging(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env.ref("product.product_delivery_02")
        cls.packaging = cls.env["product.packaging"].create(
            {
                "name": "10 pack",
                "product_id": cls.product.id,
                "qty": 10,
                "lngth": 12,
                "width": 13,
                "height": 14,
                "max_weight": 15,
            }
        )
        cls.package = cls.env["stock.quant.package"].create({})

    def test_set_dimensions_on_write(self):
        self.package.product_packaging_id = self.packaging
        self.assertRecordValues(
            self.package, [{"lngth": 12, "width": 13, "height": 14, "pack_weight": 15}]
        )
