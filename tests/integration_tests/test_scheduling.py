# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains integration tests for the Scheduler."""

# standard libraries
import importlib
from typing import List
import unittest

# 3rd party libs
from snakes.nets import Marking, MultiSet

# local sources
## PFDL base sources
from pfdl_scheduler.pfdl_base_classes import PFDLBaseClasses
from pfdl_scheduler.plugins.plugin_loader import PluginLoader
from pfdl_scheduler.scheduling.event import Event

plugin_loader = PluginLoader()
plugin_loader.load_plugins(["mf_plugin/mf_plugin"])
pfdl_base_classes = plugin_loader.get_pfdl_base_classes()

TEST_FILE_FOLDER_PATH = "pfdl_scheduler/plugins/mf_plugin/tests/test_files/valid/scheduling/"
EVENT_FILE_FOLDER_PATH = "pfdl_scheduler/plugins/mf_plugin/tests/test_files/scheduler/"


class TestScheduling(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = None

    def load_file(self, test_file_name: str) -> None:
        """Loads a file from the given path and parses it if it is a PFDL program."""

        file_path = TEST_FILE_FOLDER_PATH + test_file_name + ".pfdl"
        self.scheduler = pfdl_base_classes.get_class("Scheduler")(
            file_path,
            generate_test_ids=True,
            draw_petri_net=False,
            pfdl_base_classes=pfdl_base_classes,
        )

    def load_events_from_file(self, file_name) -> List[str]:
        file_path = EVENT_FILE_FOLDER_PATH + file_name + ".txt"
        events = []
        with open(file_path) as f:
            for line in f:
                if not line.startswith("#") and not line == "\n":
                    events.append(line)
        return events

    def check_for_finish(self, test_case_name: str):
        self.load_file(test_case_name)
        events = self.load_events_from_file(test_case_name)
        self.scheduler.start()
        self.assertTrue(self.scheduler.running)
        # fire all events except the last one. Expect that the scheduler is still running
        for event in events[:-1]:
            self.scheduler.fire_event(event)
        self.assertTrue(self.scheduler.running)

        # fire the final event. Expect the scheduler has finished afterwards
        self.scheduler.fire_event(events[-1])
        self.assertFalse(self.scheduler.running)
        petri_net = self.scheduler.petri_net_logic.petri_net

        last_place_uuid = self.scheduler.petri_net_generator.task_finished_uuid
        # check if only the last token in the MF finished place is there

        kwargs = {last_place_uuid: MultiSet(1)}
        final_marking = Marking(**kwargs)
        self.assertEqual(petri_net.get_marking(), final_marking)

    def test_finished_by_finishes(self):
        self.check_for_finish("finished_by")

    def test_finished_by_move_finishes(self):
        self.check_for_finish("finished_by_move")

    def test_finished_by_action_finishes(self):
        self.check_for_finish("finished_by_action")

    def test_multiple_event_types_finishes(self):
        self.check_for_finish("multiple_event_types")

    def test_multiple_orders_finishes(self):
        self.check_for_finish("multiple_orders")

    def test_on_done_task_finishes(self):
        self.check_for_finish("on_done_task")

    def test_parallel_tasks_finishes(self):
        self.check_for_finish("parallel_tasks")

    def test_parameters_finishes(self):
        self.check_for_finish("parameters")

    def test_picklist_task_finishes(self):
        self.check_for_finish("picklist_task")

    def test_rule_in_task_finishes(self):
        self.check_for_finish("rule_in_task")

    def test_simple_action_finishes(self):
        self.check_for_finish("simple_action")

    def test_simple_move_finishes(self):
        self.check_for_finish("simple_move")

    def test_simple_transport_finishes(self):
        self.check_for_finish("simple_transport")

    def test_started_by_finishes(self):
        self.check_for_finish("started_by")

    def test_struct_with_attribute_access_finishes(self):
        self.check_for_finish("struct_with_attribute_access")

    def test_struct_with_instance_variable_finishes(self):
        self.check_for_finish("struct_with_instance_variable")

    def test_task_constraints_finishes(self):
        self.check_for_finish("task_constraints")

    def test_service_in_task_finishes(self):
        self.check_for_finish("service_in_task")

    def test_task_repeat_finishes(self):
        self.check_for_finish("task_repeat")

    def test_task_sequence_finishes(self):
        self.check_for_finish("task_sequence")

    def test_condition_in_task_finishes(self):
        self.check_for_finish("condition_in_task")

    def test_while_loop_finishes(self):
        self.check_for_finish("while_loop")

    def test_counting_loop_finishes(self):
        self.check_for_finish("counting_loop")

    def test_parallel_loop_finishes(self):
        self.check_for_finish("parallel_loop")

    def test_struct_inheritance_finishes(self):
        self.check_for_finish("struct_inheritance")


if __name__ == "__main__":
    unittest.main()
