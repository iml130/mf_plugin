# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""This class contains plugin code to overwrite the PFDL class Task."""

# standard libraries
from typing import Dict, OrderedDict, Union, List

# 3rd party libraries
from antlr4.ParserRuleContext import ParserRuleContext

# local sources
## PFDL base sources
import pfdl_scheduler.plugins
from pfdl_scheduler.model.service import Service
from pfdl_scheduler.model.condition import Condition
from pfdl_scheduler.model.while_loop import Loop
from pfdl_scheduler.model.task_call import TaskCall
from pfdl_scheduler.model.array import Array

## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order import TransportOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order import MoveOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order import ActionOrder
from pfdl_scheduler.plugins.plugin_loader import base_class


@base_class("Task")
class Task(pfdl_scheduler.model.task.Task):
    def __init__(
        self,
        name: str = "",
        statements: List[
            Union[Service, TaskCall, Loop, Condition, TransportOrder, MoveOrder, ActionOrder]
        ] = None,
        variables: Dict[str, Union[str, Array]] = None,
        input_parameters: OrderedDict[str, Union[str, Array]] = None,
        output_parameters: List[str] = None,
        context: ParserRuleContext = None,
        started_by_expr: Union[str, Dict] = None,
        finished_by_expr: Union[str, Dict] = None,
        constraints: Union[str, Dict] = None,
        constraints_string: str = "",
    ) -> None:
        # initialize the PFDL Task class
        pfdl_scheduler.model.task.Task.__init__(
            self, name, statements, variables, input_parameters, output_parameters, context
        )

        # MF-Plugin specific additions
        self.started_by_expr: Union[str, Dict] = started_by_expr
        self.finished_by_expr: Union[str, Dict] = finished_by_expr

        self.constraints: Union[str, Dict] = {}
        if constraints:
            self.constraints = constraints

        self.constraints_string: str = constraints_string
