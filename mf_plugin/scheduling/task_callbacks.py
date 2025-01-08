# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""This file contains plugin code to overwrite the PFDL class TaskCallbacks."""

# standard libraries
from typing import Any, Callable, List, Union

# local sources
import pfdl_scheduler
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.task import Task
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order import (
    TransportOrder,
)
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order import MoveOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order import ActionOrder
from pfdl_scheduler.plugins.plugin_loader import base_class


@base_class("TaskCallbacks")
class TaskCallbacks:
    def __init__(self):
        pfdl_scheduler.scheduling.task_callbacks.TaskCallbacks.__init__(self)
        self.materialflow_started_callbacks: List[Callable[[List[Task]], Any]] = []
        self.task_started_callbacks: List[Callable[[Task], Any]] = []
        self.order_started_callbacks: List[
            Callable[[str, Union[TransportOrder, MoveOrder, ActionOrder], str]]
        ] = []
        self.started_by_callbacks: List[Callable] = []
        self.waiting_for_move_callbacks: List[Callable] = []
        self.moved_to_location_callbacks: List[Callable] = []
        self.waiting_for_action_callbacks: List[Callable] = []
        self.action_executed_callbacks: List[Callable] = []
        self.order_finished_callbacks: List[
            Callable[[str, Union[TransportOrder, MoveOrder, ActionOrder]], Any],
        ] = []
        self.finished_by_callbacks: List[Callable] = []
        self.instance_updated_callbacks: List[Callable] = []
        self.task_finished_callbacks: List[Callable[[Task], Any]] = []
        self.materialflow_finished_callbacks: List[Callable] = []

    def register_callback_materialflow_started(
        self, callback_method: List[Callable[[List[Task]], Any]]
    ) -> None:
        self.materialflow_started_callbacks.append(callback_method)

    def register_callback_task_started(self, callback_method: Callable[[Task], Any]) -> None:
        self.task_started_callbacks.append(callback_method)

    def register_callback_order_started(
        self,
        callback_methdod: Callable[[str, Union[TransportOrder, MoveOrder, ActionOrder]], Any],
    ) -> None:
        self.order_started_callbacks.append(callback_methdod)

    def register_callback_started_by(self, callback_method: Callable) -> None:
        self.started_by_callbacks.append(callback_method)

    def register_callback_waiting_for_move(self, callback_method: Callable) -> None:
        self.waiting_for_move_callbacks.append(callback_method)

    def register_callback_moved_to_location(self, callback_method: Callable) -> None:
        self.moved_to_location_callbacks.append(callback_method)

    def register_callback_waiting_for_action(self, callback_method: Callable) -> None:
        self.waiting_for_action_callbacks.append(callback_method)

    def register_callback_action_executed(self, callback_method: Callable) -> None:
        self.action_executed_callbacks.append(callback_method)

    def register_callback_order_finished(
        self,
        callback_method: Callable[[str, Union[TransportOrder, MoveOrder, ActionOrder]], Any],
    ):
        self.order_finished_callbacks.append(callback_method)

    def register_callback_finished_by(self, callback_method: Callable):
        self.finished_by_callbacks.append(callback_method)

    def register_callback_instance_updated(self, callback_method: Callable):
        self.instance_updated_callbacks.append(callback_method)

    def register_callback_task_finished(self, callback_method: Callable[[Task], Any]):
        self.task_finished_callbacks.append(callback_method)

    def register_callback_materialflow_finished(self, callback_method: Callable):
        self.materialflow_finished_callbacks.append(callback_method)
