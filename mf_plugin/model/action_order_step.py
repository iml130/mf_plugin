# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains ActionOrderStep class."""

# standard libraries
from typing import Dict, Union

# 3rd party libs
from antlr4.ParserRuleContext import ParserRuleContext

# local sources
## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.order_step import OrderStep


class ActionOrderStep(OrderStep):
    """Represents a ActionOrderStep in the MF-Plugin.

    Inherited from OrderStep. Adds parameters.

    Attributes:
        name: A string representing the name of the TransportOrderStep.
        started_by_expr: The StartedBy expression represented as Dict.
        finished_by_expr: The FinishedBy expression represented as Dict.
        parameters: A single string as parameter or a Dict of parameters of the OrderStep.
        follow_up_task_name: A string representing the name of a possible follow up task.
        context: ANTLR context object of this class.
        context_dict: Maps other attributes with ANTLR context objects.
    """

    def __init__(
        self,
        name: str = "",
        started_by_expr: Union[str, Dict] = None,
        finished_by_expr: Union[str, Dict] = None,
        parameters: Union[str, Dict] = None,
        follow_up_task_name: str = "",
        context: ParserRuleContext = None,
    ) -> None:
        """Initialize the object.

        Args:
            name: A string representing the name of the TransportOrderStep.
            started_by_expr: The StartedBy expression represented as Dict.
            finished_by_expr: The FinishedBy expression represented as Dict.
            parameters: A single string as parameter or a Dict of parameters of the OrderStep.
            follow_up_task_name: A string representing the name of a possible follow up task.
            context: ANTLR context object of this class.
        """
        super().__init__(name, started_by_expr, finished_by_expr, follow_up_task_name)

        self.parameters: Dict = parameters
        self.context: ParserRuleContext = context
        self.context_dict: Dict = {}
