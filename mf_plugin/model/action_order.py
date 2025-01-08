# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains ActionOrder class."""

# 3rd party libs
from antlr4.ParserRuleContext import ParserRuleContext

# local sources
## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order_step import ActionOrderStep


class ActionOrder:
    """Represents an ActionOrder (Action statement) in the MF-Plugin.

    Attributes:
        action_order_step_name: A string representing the name of an ActionOrderStep.
        action_order_step: The ActionOrderStep that was defined for this Order.
        context: ANTLR context object of this class.
    """

    def __init__(
        self,
        action_order_step_name: str = "",
        action_order_step: ActionOrderStep = None,
        context: ParserRuleContext = None,
    ) -> None:
        """Initialize the object.

        Args:
            action_order_step_name: A string representing the name of an ActionOrderStep.
            action_order_step: The ActionOrderStep that was defined for this Order.
            context: ANTLR context object of this class.
        """
        self.action_order_step_name: str = action_order_step_name
        self.action_order_step = action_order_step
        self.context: ParserRuleContext = context
