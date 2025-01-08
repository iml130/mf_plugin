# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""
This file contains an interface to demonstrate the use of the MF-Plugin for the PFDL.

NOTE: This file has to be placed in the root PFDL directory in order to work correctly.
"""

# standard libraries
import argparse
from typing import Dict
import json

# local sources
from pfdl_scheduler.api.service_api import ServiceAPI
from pfdl_scheduler.api.task_api import TaskAPI

from pfdl_scheduler.pfdl_base_classes import PFDLBaseClasses
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.task import Task
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.struct import Struct
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.api.order_api import OrderAPI
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.api.order_step_api import OrderStepAPI
from pfdl_scheduler.scheduler import Scheduler, Event
from pfdl_scheduler.plugins.plugin_loader import PluginLoader


def cb_task_started(task: Task, scheduler_uuid: str):
    print("Task '" + task.name + "' started!")


def cb_order_started(order_api: OrderAPI, scheduler_uuid: str):
    print(
        "A "
        + type(order_api.order).__name__
        + " with the UUID '"
        + order_api.uuid
        + "' has started"
    )


def cb_started_by(scheduler_uuid: str):
    print("StartedBy condition not satisfied yet.")


def cb_waiting_for_move(order_step_api: OrderStepAPI):
    print("Orderstep with UUID " + order_step_api.uuid + " is waiting for move")


def cb_moved_to_location(location: str, order_step_api: OrderStepAPI, scheduler_uuid: str):
    print("Moved to location '" + location + "' for Order '" + order_step_api.uuid + "'.")


def cb_waiting_for_action(order_step_api: OrderStepAPI):
    print("Orderstep with UUID " + order_step_api.uuid + " is waiting for action to be executed")


def cb_action_executed(order_step_api: OrderStepAPI, scheduler_uuid: str):
    print("Executed Action for Order '" + order_step_api.uuid + "'.")


def cb_order_finished(order_api: OrderAPI, scheduler_uuid: str):
    print("Order with the uuid '" + order_api.uuid + "' finished.")


def cb_finished_by(scheduler_uuid: str):
    print("FinishedBy condition not satisfied yet.")


def cb_instance_updated(instance_name: str, data: Dict, scheduler_uuid: str):
    print(
        "The instance '"
        + instance_name
        + "' was updated successfully with the data: \n"
        + json.dumps(data)
    )


def cb_task_finished(task_name: str, scheduler_uuid: str):
    print("Task '" + task_name + "' finished.")


class DemoInterface:
    """A dummy interface which demonstrates the use of the scheduler functions.

    At start the interface register its callback functions and variable access function
    to the scheduler. The callback functions provide a simple debug message to show
    the functionality of the scheduler.

    Attributes:
        scheduler: A Scheduler instance
        wetness: A dummy variable which is used in the PFDL examples
        parts_count: A dummy variable which is used in the PFDL examples
    """

    def __init__(self, scheduler: Scheduler) -> None:
        """Initialize the object"""
        self.scheduler: Scheduler = scheduler
        self.wetness: int = 11
        self.parts_count: int = 1

    def cb_task_started(self, task_api: TaskAPI) -> None:
        task_name = task_api.task.name
        task_uuid = task_api.uuid
        print("Task " + task_name + " with UUID '" + task_uuid + "' started")

    def cb_service_started(self, service_api: ServiceAPI) -> None:
        service_name = service_api.service.name
        service_uuid = service_api.uuid
        print("Service " + service_name + " with UUID '" + service_uuid + "' started")

    def cb_service_finished(self, service_api: ServiceAPI) -> None:
        service_name = service_api.service.name
        service_uuid = service_api.uuid
        print("Service " + service_name + " with UUID '" + service_uuid + "' finished")

    def cb_task_finished(self, task_api: TaskAPI) -> None:
        task_name = task_api.task.name
        task_uuid = task_api.uuid
        print("Task " + task_name + " with UUID '" + task_uuid + "' finished")

    def variable_access_function(self, var_name, task_context: TaskAPI) -> Struct:
        """Simulate a variable access function which returns a Struct variable.

        This dummy method simulates an access to variables from the PFDL. The returned structs
        are used in the examples folder.

        Returns:
            A struct variable corresponding to the given variable name in the given task context.
        """
        print("Request variable '" + var_name + "' from task with UUID '" + task_context.uuid + "'")
        dummy_struct = Struct()

        if var_name == "pr" or var_name == "dr":
            dummy_struct.attributes = {"wetness": self.wetness}
        elif var_name == "cr":
            dummy_struct.attributes = {"parts_count": self.parts_count}
        elif var_name == "order":
            dummy_struct.attributes = {"number_light_segments": 3}
        elif var_name == "parallel_tasks":
            dummy_struct.attributes = {"tasks": self.parts_count}
            self.parts_count += 1

        return dummy_struct

    def start(self):
        self.scheduler.register_callback_task_started(self.cb_task_started)
        self.scheduler.register_callback_service_started(self.cb_service_started)
        self.scheduler.register_callback_service_finished(self.cb_service_finished)
        self.scheduler.register_callback_task_finished(self.cb_task_finished)
        self.scheduler.register_variable_access_function(self.variable_access_function)

        self.scheduler.task_callbacks.register_callback_order_started(cb_order_started)
        self.scheduler.task_callbacks.register_callback_started_by(cb_started_by)
        self.scheduler.task_callbacks.register_callback_waiting_for_move(cb_waiting_for_move)
        self.scheduler.task_callbacks.register_callback_moved_to_location(cb_moved_to_location)
        self.scheduler.task_callbacks.register_callback_waiting_for_action(cb_waiting_for_action)
        self.scheduler.task_callbacks.register_callback_action_executed(cb_action_executed)
        self.scheduler.task_callbacks.register_callback_order_finished(cb_order_finished)
        self.scheduler.task_callbacks.register_callback_finished_by(cb_finished_by)
        self.scheduler.task_callbacks.register_callback_instance_updated(cb_instance_updated)

        self.scheduler.start()

        while self.scheduler.running:
            input_str = str(input("Wait for input:>"))
            splitted = input_str.split(",")

            if len(splitted) == 2:
                service_uuid = splitted[0]
                event_type = splitted[1]
                event = Event(event_type=event_type, data={"service_uuid": service_uuid})
                self.scheduler.fire_event(event)
            elif len(splitted) == 3:
                order_step_uuid = splitted[0]
                task = splitted[1]
                status = splitted[2]
                event = Event(
                    event_type="order_step_update",
                    data={
                        "order_step_uuid": order_step_uuid,
                        "task": task,
                        "status": status,
                    },
                )
                self.scheduler.fire_event(event)
            else:
                self.scheduler.fire_event(input_str)


def main():
    plugin_loader = PluginLoader()
    plugin_loader.load_plugins(["mf_plugin/mf_plugin"])

    pfdl_base_classes = plugin_loader.get_pfdl_base_classes()

    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument("file_path", type=str, help="the path for the PFDL file.")
    parser.add_argument(
        "--test_ids",
        action="store_true",
        help="services and tasks get test ids starting from 0.",
    )
    args = parser.parse_args()

    scheduler = pfdl_base_classes.get_class("Scheduler")(
        args.file_path,
        args.test_ids,
        pfdl_base_classes=pfdl_base_classes,
    )

    demo_interface = DemoInterface(scheduler)
    demo_interface.start()


if __name__ == "__main__":
    main()
