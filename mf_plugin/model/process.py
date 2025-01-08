# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""This class contains plugin code to overwrite the PFDL class Process."""

# standard libraries
from typing import Dict, List, Union, TypeVar

# local sources
## PFDL base sources
import pfdl_scheduler.model
from pfdl_scheduler.model.instance import Instance
import pfdl_scheduler.plugins

from pfdl_scheduler.model.struct import Struct
from pfdl_scheduler.model.task import Task

### only for unit tests
from pfdl_scheduler.model.process import Process

## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order_step import TransportOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order_step import MoveOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order_step import ActionOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.rule import Rule
from pfdl_scheduler.plugins.plugin_loader import base_class


@base_class("Process")
class Process(pfdl_scheduler.model.process.Process):
    def __init__(
        self,
        structs: Dict[str, Struct] = None,
        tasks: Dict[str, Task] = None,
        start_task_name: str = "mainTask",
    ) -> None:
        pfdl_scheduler.model.process.Process.__init__(
            self, structs, tasks, start_task_name=start_task_name
        )

        self.instances: Dict[str, Instance] = {}
        self.rules: Dict[str, Rule] = {}
        self.tasks: Dict[str, Task] = {}
        self.transport_order_steps: Dict[str, TransportOrderStep] = {}
        self.move_order_steps: Dict[str, MoveOrderStep] = {}
        self.action_order_steps: Dict[str, ActionOrderStep] = {}

    def get_instances(self, type_of_instance: str) -> List[Instance]:
        """Returns a List of all instance that has the given type.

        The returned list contains all instances of the given type and all
        child types.
        """

        instances = []
        for instance in self.instances.values():
            struct_name = instance.struct_name
            parent_struct = ""
            while struct_name != None and struct_name != "":
                parent_struct = struct_name
                struct_name = self.structs[struct_name].parent_struct_name

                if parent_struct == type_of_instance:
                    instances.append(instance)
                    break

        return instances
