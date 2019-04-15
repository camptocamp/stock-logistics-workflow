# -*- coding: utf-8 -*-
# Copyright 2013-2019 Camptocamp SA - Alexandre Fayolle
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, models, fields
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare


class StockPickingSplit(models.TransientModel):
    _name = 'stock.picking.split'

    picking_id = fields.Many2one(
        'stock.picking',
        string='Picking',
        required=True,
        default=lambda s: s.env.context.get('active_id', False)
    )
    line_ids = fields.One2many(
        'stock.picking.split.line',
        'split_id',
        string='Split Operations',
    )

    @api.model
    def create(self, vals):
        rec = super(StockPickingSplit, self).create(vals)
        rec._generate_lines()
        return rec

    @api.multi
    def process(self):
        self.ensure_one()
        uom_dp = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        picking = self.picking_id
        reserve = False
        if picking.pack_operation_ids:
            reserve = True
            picking.do_unreserve()
        split_picking = picking.copy(
            {
                'name': '/',
                'move_lines': [],
                'pack_operation_ids': [],
            }
        )
        # Handle the case where there are several stock.move with the same
        # product+UoM. We summed the qtys for all these moves in the wizard,
        # and now we need to spread back the qtys among the different moves
        # with the same product+UoM.
        product_split = {}
        for line in self.line_ids:
            key = (line.product_id, line.product_uom_id)
            product_split[key] = line.split_qty
        new_move_ids = []
        for move in picking.move_lines:
            if move.state in ('cancel', 'done'):
                continue
            key = (move.product_id, move.product_uom)
            to_split = min(product_split[key], move.product_uom_qty)
            # if to_split > 0
            if float_compare(to_split, 0, precision_digits=uom_dp) == 1:
                product_split[key] -= to_split
                # the 'split()' method expect the qty to be converted in the
                # UoM of the product
                to_split_converted = move.product_uom._compute_quantity(
                    to_split, move.product_id.uom_id)
                new_move_ids.append(move.split(to_split_converted))
        self.env['stock.move'].browse(new_move_ids).write(
            {'picking_id': split_picking.id}
        )
        picking.message_post(
            body=_("Split picking <em>%s</em> <b>created</b>.") %
            (split_picking.name)
        )
        split_picking.message_post(
            body=_("Split from picking <em>%s</em> <b>created</b>.") %
            (picking.name)
        )
        split_picking.action_confirm()
        if reserve:
            picking.action_assign()
            split_picking.action_assign()
        return split_picking.id

    def _generate_lines(self):
        self.ensure_one()
        line_ids = self.env['stock.picking.split.line']
        product_qty = {}
        product_availability = {}
        for move in self.picking_id.move_lines:
            if move.state in ('cancel', 'done'):
                continue
            reserved_availability = move.product_id.uom_id._compute_quantity(
                move.reserved_availability, move.product_uom)
            key = (move.product_id, move.product_uom)
            if key not in product_qty:
                product_qty[key] = move.product_uom_qty
                product_availability[key] = reserved_availability
            else:
                product_qty[key] += move.product_uom_qty
                product_availability[key] += reserved_availability
        for key, qty in product_qty.items():
            product, uom = key
            vals = {'picking_id': self.picking_id.id,
                    'product_qty': qty,
                    'split_qty': product_availability[key],
                    'product_id': product.id,
                    'product_uom_id': uom.id,
                    }
            line_ids |= self.env['stock.picking.split.line'].create(vals)
        self.line_ids = line_ids


class StockPickingSplitLine(models.TransientModel):
    _name = 'stock.picking.split.line'

    split_id = fields.Many2one('stock.picking.split',
                               ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', 'Product', ondelete="cascade", readonly=True
    )
    product_uom_id = fields.Many2one(
        'product.uom', 'Unit of Measure', readonly=True
    )
    product_qty = fields.Float(
        'Total', default=0.0,
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
        readonly=True
    )
    split_qty = fields.Float(
        'Split', default=0.0,
        digits=dp.get_precision('Product Unit of Measure'), required=True
    )

    @api.constrains('product_qty', 'split_qty')
    def _check_qty(self):
        uom_dp = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for rec in self:
            # if qty to split is > to qty of the move
            if float_compare(
                    rec.split_qty, rec.product_qty,
                    precision_digits=uom_dp) == 1:
                raise ValidationError(
                    _('Split quantity for product %s '
                      'must be less than %.3f') %
                    (rec.product_id.name, rec.product_qty)
                )
            # if qty to split is negative
            if float_compare(rec.split_qty, 0, precision_digits=uom_dp) == -1:
                raise ValidationError(
                    _('Split quantity for product %s '
                      'must be greater than or equal to 0') %
                    (rec.product_id.name)
                )
