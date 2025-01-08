# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains OrderStep class."""

# standard libraries
from typing import Dict, Union

# 3rd party libs
from antlr4.ParserRuleContext import ParserRuleContext


class OrderStep:
    """Base class for the OrderSteps in the MF-Plugin.

    Both OrderSteps (ActionOrderStep and TransportOrderStep) have a name and can
    triggered by expressions.

    Attributes:
        name: A string representing the name of the OrderStep.
        started_by_expr: The StartedBy expression represented as Dict.
        finished_by_expr: The FinishedBy expression represented as Dict.
        follow_up_task_name: A string representing the name of a possible follow up task.
        context: ANTLR context object of this class.
    """

    def __init__(
        self,
        name: str = "",
        started_by_expr: Union[str, Dict] = None,
        finished_by_expr: Union[str, Dict] = None,
        follow_up_task_name: str = "",
        context: ParserRuleContext = None,
    ) -> None:
        """Initialize the object.

        Args:
            name: A string representing the name of the OrderStep.
            started_by_expr: The StartedBy expression represented as Dict.
            finished_by_expr: The FinishedBy expression represented as Dict.
            follow_up_task_name: A string representing the name of a possible follow up task.
            context: ANTLR context object of this class.
        """
        self.name: str = name

        self.started_by_expr: Union[str, Dict] = started_by_expr
        self.finished_by_expr: Union[str, Dict] = finished_by_expr
        self.follow_up_task_name: str = follow_up_task_name

        self.context: ParserRuleContext = context
