# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains MoveOrderStep class."""

# standard libraries
from typing import Dict, Union

# 3rd party libs
from antlr4.ParserRuleContext import ParserRuleContext

# local sources
## MF-Plugin sources
from pfdl_scheduler.model.instance import Instance
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.order_step import OrderStep


class MoveOrderStep(OrderStep):
    """Represents a MoveOrderStep in the MF-Plugin.

    Inherited from OrderStep. Adds parameters and location.

    Attributes:
        name: A string representing the name of the MoveOrderStep.
        started_by_expr: The StartedBy expression represented as Dict.
        finished_by_expr: The FinishedBy expression represented as Dict.
        parameters: A single string as parameter or a Dict of parameters of the OrderStep.
        location_name: A string representing the location name this MoveOrderStep is assigned to.
        location: The location this MoveOrderStep is assigned to.
        follow_up_task_name: A string representing the name of a possible follow up task.
        context: ANTLR context object of this class.
    """

    def __init__(
        self,
        name: str = "",
        started_by_expr: Union[str, Dict] = None,
        finished_by_expr: Union[str, Dict] = None,
        parameters: Union[str, Dict] = None,
        location_name: str = "",
        location: Instance = None,
        follow_up_task_name: str = "",
        context: ParserRuleContext = None,
    ) -> None:
        """Initialize the object.

        Args:
            name: A string representing the name of the MoveOrderStep.
            started_by_expr: The StartedBy expression represented as Dict.
            finished_by_expr: The FinishedBy expression represented as Dict.
            parameters: A single string as parameter or a Dict of parameters of the OrderStep.
            location_name: A string representing the location name this MoveOrderStep is assigned to.
            location: The location this MoveOrderStep is assigned to.
            follow_up_task_name: A string representing the name of a possible follow up task.
            context: ANTLR context object of this class.
        """
        super().__init__(name, started_by_expr, finished_by_expr, follow_up_task_name)

        self.parameters: Union[str, Dict] = parameters
        self.location_name: str = location_name
        self.location: Instance = location
        self.context: ParserRuleContext = context
        self.context_dict: Dict = {}
