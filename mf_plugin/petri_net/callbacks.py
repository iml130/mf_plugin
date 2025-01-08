# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""This file contains plugin code to overwrite the PFDL class PetriNetCallbacks."""

# standard libraries
from typing import Any, Callable
from dataclasses import dataclass

# local sources
## PFDL base sources
import pfdl_scheduler.plugins

from pfdl_scheduler.api.task_api import TaskAPI

## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.api.order_api import OrderAPI
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.api.order_step_api import OrderStepAPI
from pfdl_scheduler.plugins.plugin_loader import base_class


@dataclass
@base_class("PetriNetCallbacks")
class PetriNetCallbacks:
    """Internal MF-Plugin callback functions that can be registered in the petri net.

    Attributes:
        PFDL callbacks:
            task_started: Callback function which is called when a task is started.
            service_started: Callback function which is called when a service is started.
            service_finished: Callback function which is called when a task is started.
            condition_started: Callback function which is called when a task is started.
            while_loop_started: Callback function which is called when a while loop is started.
            counting_loop_started: Callback function which is called when a counting loop is started.
            parallel_loop_started: Callback function which is called when a parallel loop is started.
            task_finished: Callback function which is called when a task is finished.
        MF-Plugin callbacks:
            order_started: Callback function which is called when an order is started.
            started_by: Callback function which is called when a StartedBy condition is reached.
            finished_by: Callback function which is called when a FinishedBy condition is reached.
            waiting_for_move: Callback function which is called when a move is required to continue.
            moved_to_location: Callback function which is called when a move location is reached.
            waiting_for_action: Callback function which is called when an action is required to continue.
            action_executed: Callback function which is called when a an action was executed.
            order_finished: Callback function which is called when an order is finished.

    """

    order_started: Callable[[OrderAPI], Any] = None
    started_by: Callable[[TaskAPI, OrderStepAPI], Any] = None
    finished_by: Callable[[TaskAPI, OrderStepAPI], Any] = None
    waiting_for_move: Callable[[OrderStepAPI, TaskAPI], Any] = None
    moved_to_location: Callable[[OrderStepAPI], Any] = None
    waiting_for_action: Callable[[OrderStepAPI, TaskAPI], Any] = None
    action_executed: Callable[[OrderStepAPI], Any] = None
    order_finished: Callable[[OrderStepAPI], Any] = None
