# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""This file contains plugin code to overwrite the PFDL class PetriNetLogic."""

# local sources
## PFDL base sources
import pfdl_scheduler.plugins
from pfdl_scheduler.plugins.plugin_loader import base_class
from pfdl_scheduler.scheduling.event import Event

### only for unit tests
from pfdl_scheduler.petri_net.logic import PetriNetLogic

## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.petri_net import generator


@base_class("PetriNetLogic")
class PetriNetLogic(pfdl_scheduler.petri_net.logic.PetriNetLogic):
    def __init__(
        self,
        petri_net_generator: generator,
        draw_net: bool = True,
        file_name: str = "",
    ):
        pfdl_scheduler.petri_net.logic.PetriNetLogic.__init__(
            self, petri_net_generator, draw_net, file_name
        )
        self.uuids_per_task = []

    def fire_event(self, event: Event) -> bool:
        if pfdl_scheduler.petri_net.logic.PetriNetLogic.fire_event(self, event):
            return True
        task_uuid = event.data["task"]
        if event.event_type == "started_by":
            if "order_step" in event.data:
                order_step = event.data["order_step"]
                name_in_petri_net = self.uuids_per_task[task_uuid][order_step]["started_by"]
            else:
                name_in_petri_net = self.uuids_per_task[task_uuid]["started_by"]
        elif event.event_type == "finished_by":
            if "order_step" in event.data:
                order_step_name = event.data["order_step"]
                name_in_petri_net = self.uuids_per_task[task_uuid][order_step_name]["finished_by"]
            else:
                name_in_petri_net = self.uuids_per_task[task_uuid]["finished_by"]
        elif event.event_type == "order_step_update":
            order_step_uuid = event.data["order_step_uuid"]
            agv_status = event.data["status"]
            name_in_petri_net = self.uuids_per_task[task_uuid][order_step_uuid][agv_status]

        if self.petri_net.has_place(name_in_petri_net):
            self.petri_net.place(name_in_petri_net).add(1)
            self.draw_petri_net()
            self.evaluate_petri_net()
            return True
        return False
