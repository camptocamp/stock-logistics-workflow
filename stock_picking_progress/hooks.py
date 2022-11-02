# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

logger = logging.getLogger(__name__)


def column_exists(cr, args):
    column_exists_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name=%(table)s AND
        column_name=%(column)s;
    """
    cr.execute(column_exists_query, args)
    return cr.fetchone()


def setup_move_line_completion(cr):
    table = "stock_move_line"
    column = "completion"
    args = {"table": table, "column": column}
    if column_exists(cr, args):
        logger.info(f"{column} already exists on {table}, skipping setup")
        return
    add_column_query = """
        ALTER TABLE stock_move_line
        ADD COLUMN completion float
    """
    logger.info(f"creating {column} on table {table}")
    cr.execute(add_column_query, args)
    fill_column_query = """
        UPDATE stock_move_line
        SET completion = CASE
            WHEN (product_uom_qty IS NULL or product_uom_qty = 0.0) THEN 0.0
            ELSE (qty_done / product_uom_qty) * 100
        END;
    """
    logger.info(f"filling up {column} on {table}")
    cr.execute(fill_column_query, args)


def setup_picking_completion(cr):
    table = "stock_picking"
    column = "completion"
    args = {"table": table, "column": column}
    if column_exists(cr, args):
        logger.info(f"{column} already exists on {table}, skipping setup")
        return
    add_column_query = """
        ALTER TABLE stock_picking
        ADD COLUMN completion float
    """
    logger.info(f"creating {column} on table {table}")
    cr.execute(add_column_query, args)
    fill_column_query = """
        UPDATE stock_picking p
        SET completion = subquery.avg_completion
        FROM (
            SELECT sml.picking_id, avg(sml.completion) as avg_completion
            FROM stock_move_line sml
            GROUP BY sml.picking_id
        ) as subquery
        WHERE p.id = subquery.picking_id;
    """
    logger.info(f"filling up {column} on {table}")
    cr.execute(fill_column_query)


def pre_init_hook(cr):
    setup_move_line_completion(cr)
    setup_picking_completion(cr)
