#  Copyright 2025 Camptocamp SA
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute("""
        UPDATE product_template
            SET description_picking = (
               SELECT description_warehouse
               FROM product_product
               WHERE product_template.id = product_product.product_tmpl_id limit 1
               )
        ;
    """)
