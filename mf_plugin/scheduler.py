# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""This file contains plugin code to overwrite the PFDL class Scheduler."""

# standard libraries
import time
import uuid
import threading
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

from pfdl_scheduler.pfdl_base_classes import PFDLBaseClasses
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.petri_net.generator import PetriNetGenerator
from pfdl_scheduler.plugins.plugin_loader import base_class

# 3rd party libs
# Temporary fix because this module cannot be imported in
# the integration test
try:
    from croniter import croniter
except ImportError:
    pass

# local sources
## PFDL base sources
from pfdl_scheduler.api.task_api import TaskAPI
from pfdl_scheduler.scheduling.event import Event
from pfdl_scheduler.utils.parsing_utils import parse_program
from pfdl_scheduler.model.counting_loop import CountingLoop
import pfdl_scheduler.scheduler

## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.api.order_api import OrderAPI
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.api.order_step_api import OrderStepAPI

from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.task import Task

from pfdl_scheduler.plugins.mf_plugin.mf_plugin.scheduling.task_callbacks import TaskCallbacks
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.helpers import (
    execute_mf_plugin_expression,
    evaluate_rule,
)


@base_class("Scheduler")
class Scheduler(pfdl_scheduler.scheduler.Scheduler):
    """Overwrites the PFDL Scheduler's `Scheduler` class"""

    def __init__(
        self,
        pfdl_program: str,
        generate_test_ids: bool = False,
        draw_petri_net: bool = True,
        scheduler_uuid: str = "",
        dashboard_host_address: str = "",
        pfdl_base_classes: PFDLBaseClasses = PFDLBaseClasses("pfdl_scheduler"),
    ):
        """Initialize the object.

        This method overwrites the PFDL Scheduler's init function.

        Args:
            pfdl_program: A path to the PFDL file or directly the PFDL program as a string.
            generate_test_ids: A boolean indicating whether specific test ids should be generated instead of uuids.
            draw_petri_net: A boolean indicating whether the petri net should be drawn.
            scheduler_uuid: A unique ID to identify the Scheduer / Production Order.
        """
        # init scheduler attributes with all PFDL attributes and additional MF-Plugin attributes
        self.init_scheduler(
            scheduler_uuid,
            generate_test_ids,
            pfdl_base_classes.get_class("PetriNetGenerator")(pfdl_base_classes=pfdl_base_classes),
            pfdl_base_classes.get_class("TaskCallbacks")(),
        )

        self.pfdl_file_valid, self.process, pfdl_string = parse_program(
            pfdl_program, pfdl_base_classes=pfdl_base_classes
        )
        if self.pfdl_file_valid:
            # use MF-Plugin petri net generator
            self.petri_net_generator = pfdl_base_classes.get_class("PetriNetGenerator")(
                "",
                generate_test_ids=self.generate_test_ids,
                draw_net=draw_petri_net,
                file_name=self.scheduler_uuid,
                pfdl_base_classes=pfdl_base_classes,
            )

            # check if test ids have to be used inside the petri net generator
            # if test_ids is set to true,set the counter to 0 (any other value than -1 will start the counting)
            if generate_test_ids:
                self.petri_net_generator.order_step_test_id_counter = 0

            self.active_order_steps = self.petri_net_generator.order_steps
            self.apis_per_structure["task_apis"] = self.petri_net_generator.task_apis
            self.apis_per_structure["order_apis"] = self.petri_net_generator.orders
            self.apis_per_structure["order_step_apis"] = self.petri_net_generator.order_steps

            # call scheduling setup
            pfdl_scheduler.scheduler.Scheduler.setup_scheduling(
                self, draw_petri_net, pfdl_base_classes.get_class("PetriNetLogic")
            )
            self.petri_net_logic.uuids_per_task = self.petri_net_generator.uuids_per_task

            self.set_timer_for_time_instances()

    def init_scheduler(
        self,
        scheduler_uuid: str,
        generate_test_ids: bool,
        petri_net_generator: PetriNetGenerator,
        task_callbacks: TaskCallbacks,
    ) -> None:
        """Overwrites method from PFDL Scheduler to additionally initialize MF-Plugin related attributes."""
        # call the original method from the PFDL scheduler
        pfdl_scheduler.scheduler.Scheduler.init_scheduler(
            self,
            scheduler_uuid,
            generate_test_ids,
            petri_net_generator,
            task_callbacks,
        )

        # additional MF-Plugin-exclusive attributes
        self.active_tasks: List[TaskAPI] = []
        self.active_order_steps: List[OrderStepAPI] = []
        self.apis_per_structure: Dict[str, List[TaskAPI | OrderAPI | OrderStepAPI]] = {
            "task_apis": [],
            "order_apis": [],
            "order_step_apis": [],
        }
        ## for time instances
        self.starting_time: float = time.time()
        self.time_instance_timers: list[threading.Timer] = []

    def register_for_petrinet_callbacks(self) -> None:
        """Overwrites method from PFDL Scheduler to register MF-Plugin callbacks too."""
        # call the original method from the PFDL scheduler
        pfdl_scheduler.scheduler.Scheduler.register_for_petrinet_callbacks(self)

        # additional MF-Plugin-exclusive callbacks
        callbacks = self.petri_net_generator.callbacks
        callbacks.order_started = self.on_order_started
        callbacks.started_by = self.on_started_by
        callbacks.finished_by = self.on_finished_by
        callbacks.waiting_for_move = self.on_waiting_for_move
        callbacks.moved_to_location = self.on_moved_to_location
        callbacks.waiting_for_action = self.on_waiting_for_action
        callbacks.action_executed = self.on_action_executed
        callbacks.order_finished = self.on_order_finished

    def set_timer_for_time_instances(self) -> None:
        """Setup timers and callback method for each Time instance."""
        time_instances = self.process.get_instances("Time")
        for time_instance in time_instances:
            timing = time_instance.attributes["timing"]
            current_time = time.time()

            # determine timer length
            cron_time = croniter(timing, start_time=datetime.today()).get_next(datetime)
            next_execution = cron_time.timestamp() - current_time

            # register callback when timer of this instance is up
            timer = threading.Timer(
                next_execution, self.update_instance, [time_instance.name, {"value": True}]
            )
            # store the timers so they could also be canceled manually
            self.time_instance_timers.append(timer)
            timer.start()

    def update_instance(self, instance_name: str, new_values: Dict) -> bool:
        """Updates the given instance with the given values.

        The new values should contain key value pairs (name of the attribute and the value).
        It is possible that the attribute refers to another instance so it is also possible
        that the value is the JSON definition of an instance.

        Returns:
            True if the instance_name refers to a known instance and the values where valid.
        """
        success = False
        if instance_name in self.process.instances:
            current_time = time.time()
            instance = self.process.instances[instance_name]
            instance.attributes["time"] = current_time - self.starting_time
            success = True

            # update instance with the new values passed
            for attribute, value in new_values.items():
                if attribute in instance.attributes.keys():
                    instance.attributes[attribute] = value
                else:
                    print(f"Instance {instance_name} has no attribute {attribute}!")

            # we updated an instance so it could be possible that an expression is now satisfied
            # in the following, reevaluate the expressions for all active tasks and order steps
            for task_api in self.active_tasks:
                if task_api.task.started_by_expr and execute_mf_plugin_expression(
                    task_api.task.started_by_expr, self.process.instances, self.process.rules
                ):
                    task_started_by_event = Event(
                        event_type="started_by", data={"task": task_api.uuid}
                    )
                    self.fire_event(task_started_by_event)
                if task_api.task.finished_by_expr and execute_mf_plugin_expression(
                    task_api.task.finished_by_expr, self.process.instances, self.process.rules
                ):
                    task_finished_by_event = Event(
                        event_type="finished_by", data={"task": task_api.uuid}
                    )
                    self.fire_event(task_finished_by_event)

            for order_step_api in self.active_order_steps:
                if order_step_api.order_step.started_by_expr and execute_mf_plugin_expression(
                    order_step_api.order_step.started_by_expr,
                    self.process.instances,
                    self.process.rules,
                ):
                    order_started_by_event = Event(
                        event_type="started_by",
                        data={"task": task_api.uuid, "order_step": order_step_api.uuid},
                    )
                    self.fire_event(order_started_by_event)
                if order_step_api.order_step.finished_by_expr and execute_mf_plugin_expression(
                    order_step_api.order_step.finished_by_expr,
                    self.process.instances,
                    self.process.rules,
                ):
                    order_finished_by_event = Event(
                        event_type="finished_by",
                        data={"task": task_api.uuid, "order_step": order_step_api.uuid},
                    )
                    self.fire_event(order_finished_by_event)
            self.on_instance_updated(instance_name, new_values)

        return success

    def fire_event(self, event: Union[Event, str]) -> bool:
        """Overwrites method from PFDL Scheduler to allow events in JSON format.

        Returns:
            True if the event could be successfully fired.
        """
        if isinstance(event, str):
            event = Event.from_json(event)
            if not event:
                return False

        # call the original method from the PFDL scheduler
        success = pfdl_scheduler.scheduler.Scheduler.fire_event(self, event)

        if not success and event.event_type == "instance_update":
            # An instance update. Not awaited by the scheduler but update the instance anyway
            success = self.update_instance(event.data["instance_name"], event.data["new_values"])

        return success

    def on_task_started(self, task_api: TaskAPI) -> None:
        """Overwrites PFDL Scheduler method to take care of active tasks and contexts."""
        self.active_tasks.append(task_api)

        # save old task uuid
        old_uuid = task_api.uuid

        # call the original method from the PFDL scheduler
        pfdl_scheduler.scheduler.Scheduler.on_task_started(self, task_api)

        # set values for new uuid and remove old values (if old and new uuid differ)
        # do this only for tasks that uses MF-Plugin features (has uuids_per_task dict set up)
        if old_uuid in self.petri_net_logic.uuids_per_task and old_uuid != task_api.uuid:
            self.petri_net_logic.uuids_per_task[task_api.uuid] = (
                self.petri_net_logic.uuids_per_task[old_uuid]
            )
            del self.petri_net_logic.uuids_per_task[old_uuid]

    def on_order_started(self, order_api: OrderAPI) -> None:
        """Executes Scheduling logic when an Order is started."""
        if order_api.in_loop:
            # generate new uuids because this order is repeatedly started in a loop

            if order_api.first_loop_iteration:
                # only update uuids if this is not the first loop iteration
                order_api.first_loop_iteration = False

            else:
                order_api.uuid = str(uuid.uuid4())

                # TODO check if MoveOrder / ActionOrder work correctly in Loop
                order_step_names = order_api.order.pickup_tos_names.copy()
                order_step_names += order_api.order.delivery_tos_names.copy()

                task_api_uuid = order_api.task_context.uuid

                # generate new uuids for all order steps
                for order_step_name in order_step_names:
                    order_step_api = next(
                        api
                        for api in self.petri_net_generator.order_steps
                        if api.order_step.name == order_step_name
                    )
                    old_order_step_uuid = order_step_api.uuid
                    if self.generate_test_ids:
                        order_step_api.uuid = str(
                            self.petri_net_generator.order_step_test_id_counter
                        )
                        self.petri_net_generator.order_step_test_id_counter += 1
                    else:
                        order_step_api.uuid = str(uuid.uuid4())

                    if task_api_uuid in self.petri_net_logic.uuids_per_task:
                        uuid_dict = self.petri_net_logic.uuids_per_task[task_api_uuid]
                        if old_order_step_uuid in uuid_dict:
                            uuid_dict[order_step_api.uuid] = uuid_dict.pop(old_order_step_uuid)

        for callback_method in self.task_callbacks.order_started_callbacks:
            callback_method(order_api, self.scheduler_uuid)

    def on_started_by(self, task_api: TaskAPI, order_step_api: OrderStepAPI = None) -> None:
        """Executes Scheduling logic when a StartedBy statement is reached."""

        awaited_event: Event = None
        object_to_call_event_for = None
        event_was_called_for_task: bool = order_step_api is None
        # StartedBy for a Task
        if event_was_called_for_task:
            awaited_event = Event("started_by", {"task": task_api.uuid})
            object_to_call_event_for = task_api.task
        # StartedBy for an OrderStep
        else:
            awaited_event = Event(
                "started_by", {"task": task_api.uuid, "order_step": order_step_api.uuid}
            )
            object_to_call_event_for = order_step_api.order_step

        # check if StartedBy is satisfied
        self.awaited_events.append(awaited_event)
        if execute_mf_plugin_expression(
            object_to_call_event_for.started_by_expr,
            self.process.instances,
            self.process.rules,
        ):
            self.fire_event(awaited_event)
        else:
            # add the task to the active tasks so the expression can be evaluated again on instance updates
            if event_was_called_for_task:
                self.active_tasks.append(task_api)

            # only call functions if StartedBy is not satisfied
            for callback_method in self.task_callbacks.started_by_callbacks:
                callback_method(self.scheduler_uuid)

    def on_finished_by(self, task_api: Task, order_step_api: OrderStepAPI = None) -> None:
        """Executes Scheduling logic when a FinishedBy statement is reached."""
        awaited_event = None
        object_to_call_event_for = None

        # FinishedBy for a Task
        if order_step_api is None:
            awaited_event = Event("finished_by", {"task": task_api.uuid})
            object_to_call_event_for = task_api.task

        # FinishedBy for an OrderStep
        else:
            awaited_event = Event(
                "finished_by", {"task": task_api.uuid, "order_step": order_step_api.uuid}
            )
            object_to_call_event_for = order_step_api.order_step

        # check if FinishedBy is satisfied
        self.awaited_events.append(awaited_event)
        if execute_mf_plugin_expression(
            object_to_call_event_for.finished_by_expr,
            self.process.instances,
            self.process.rules,
        ):
            self.fire_event(awaited_event)
        else:
            # only call functions if FinishedBy is not satisfied
            for callback_method in self.task_callbacks.finished_by_callbacks:
                callback_method(self.scheduler_uuid)

    def on_waiting_for_move(self, order_step_api: OrderStepAPI, task_api: TaskAPI) -> None:
        """Executes Scheduling logic when the net is waiting for a move."""
        # declare event to wait for
        awaited_event = Event(
            "order_step_update",
            {
                "order_step_uuid": order_step_api.uuid,
                "task": task_api.uuid,
                "status": "moved_to_location",
            },
        )
        self.awaited_events.append(awaited_event)

        for callback_method in self.task_callbacks.waiting_for_move_callbacks:
            callback_method(order_step_api)

    def on_moved_to_location(self, order_step_api: OrderStepAPI) -> None:
        """Executes Scheduling logic when a location was reached."""
        for callback_method in self.task_callbacks.moved_to_location_callbacks:
            callback_method(
                order_step_api.order_step.location_name, order_step_api, self.scheduler_uuid
            )

    def on_waiting_for_action(self, order_step_api: OrderStepAPI, task_api: TaskAPI) -> None:
        """Executes Scheduling logic when the net is waiting for an action."""
        # declare event to wait for
        awaited_event = Event(
            "order_step_update",
            {
                "order_step_uuid": order_step_api.uuid,
                "task": task_api.uuid,
                "status": "action_executed",
            },
        )
        self.awaited_events.append(awaited_event)

        for callback_method in self.task_callbacks.waiting_for_action_callbacks:
            callback_method(order_step_api)

    def on_action_executed(self, order_step_api: OrderStepAPI) -> None:
        """Executes Scheduling logic when an action was executed."""
        for callback_method in self.task_callbacks.action_executed_callbacks:
            callback_method(order_step_api, self.scheduler_uuid)

    def on_order_finished(self, order_api: OrderAPI) -> None:
        """Executes Scheduling logic when an Order is finished."""
        for callback_method in self.task_callbacks.order_finished_callbacks:
            callback_method(order_api, self.scheduler_uuid)

    def on_instance_updated(self, instance_name: str, data: Dict) -> None:
        """Handles incoming instance updates."""
        for callback_method in self.task_callbacks.instance_updated_callbacks:
            callback_method(instance_name, data, self.scheduler_uuid)

    def get_loop_limit(self, loop: CountingLoop, task_context: TaskAPI) -> int:
        """Overwrites PFDL Scheduler method to enable instance variables as loop limit."""
        if (
            isinstance(loop.limit, List)
            and len(loop.limit) >= 2
            and loop.limit[0] in self.process.instances.keys()  # check if instance and no variable
        ):
            # MF-Plugin instance
            return execute_mf_plugin_expression(
                loop.limit, self.process.instances, self.process.rules
            )
        return pfdl_scheduler.scheduler.Scheduler.get_loop_limit(self, loop, task_context)

    def on_task_finished(self, task_api: TaskAPI) -> None:
        """Overwrites PFDL Scheduler method to take care of active tasks and contexts."""
        self.active_tasks.remove(task_api)
        pfdl_scheduler.scheduler.Scheduler.on_task_finished(self, task_api)
        if not self.running:
            # the mainTask has been finished. Stop all timing instances that are still running
            for timer in self.time_instance_timers:
                if timer.is_alive():
                    timer.cancel()

    def execute_expression(self, expression: Dict, task_context: TaskAPI) -> Any:
        """Overwrites PFDL Scheduler method to support rule calls in expressions."""
        if isinstance(expression, Tuple):
            return evaluate_rule(expression, self.process.instances, self.process.rules)
        # decide here whether instance or variable
        # TODO find a better way to compare / handle different types of expression
        if isinstance(expression, List) and len(expression) == 2:
            # check whether it is an instance or a variable
            identifier = expression[0]
            if identifier in self.process.instances:
                # is an instance, execute MF-Plugin expression
                return execute_mf_plugin_expression(
                    expression, self.process.instances, self.process.rules
                )

        return pfdl_scheduler.scheduler.Scheduler.execute_expression(self, expression, task_context)
