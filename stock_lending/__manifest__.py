# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Stock lending',
    'summary': 'Enable lending and borrowing of stock',
    'version': '14.0.1.0.0',
    'category': 'Stock',
    'author': 'Camptocamp',
    'website': 'http://www.camptocamp.com/',
    'license': 'AGPL-3',
    'depends': [
        'stock',
    ],
    'data': [
        'views/stock_picking.xml',
        'views/stock_picking_type.xml',
    ],
}
