# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains MoveOrder class."""

# 3rd party libs
from antlr4.ParserRuleContext import ParserRuleContext

# local sources
## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order_step import MoveOrderStep


class MoveOrder:
    """Represents a MoveOrder (Move statement) in the MF-Plugin.

    Attributes:
        move_order_step_name: A string representing the name of an MoveOrderStep.
        move_order_step: The MoveOrderStep that was defined for this Order.
        context: ANTLR context object of this class.
    """

    def __init__(
        self,
        move_order_step_name: str = "",
        move_order_step: MoveOrderStep = None,
        context: ParserRuleContext = None,
    ) -> None:
        """Initialize the object.

        Args:
            move_order_step_name: A string representing the name of an MoveOrderStep.
            move_order_step: The MoveOrderStep that was defined for this Order.
            context: ANTLR context object of this class.
        """
        self.move_order_step_name: str = move_order_step_name
        self.move_order_step: MoveOrderStep = move_order_step
        self.context: ParserRuleContext = context
