#  Copyright 2025 Camptocamp SA
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute("""
        UPDATE product_template
            SET description_picking =
                CASE
                    WHEN description_picking IS NOT NULL THEN
                        description_picking || '\n' || description_warehouse
                    ELSE
                        description_warehouse
                END
            WHERE description_warehouse IS NOT NULL;
    """)
