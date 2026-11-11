- Move the batch position (`batch_position`, the numbering of the moves of
  a batch transfer and the sequencing of the transfers in their batch) to a
  separate `stock_picking_batch_move_position` module, so that this module no
  longer depends on `stock_picking_batch`.
