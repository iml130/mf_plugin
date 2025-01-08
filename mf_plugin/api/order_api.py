# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains the OrderAPI class."""

# standard libraries
from typing import Union
import uuid

# local sources
## PFDL base sources
from pfdl_scheduler.api.task_api import TaskAPI

## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order import TransportOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order import MoveOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order import ActionOrder


class OrderAPI:
    """Represents a started Order.

    Represents a specific entity of a started Order. OrderAPI objects are passed to
    callbacks for order start and finish.

    Attributes.
        uuid: A UUID4 which is generated at object creation and is used in the scheduling.
        order: The Order (TransportOrder, MoveOrder or ActionOrder) that is executed.
        task_context: The corresponding Task(API) this Order is executed in.
        in_loop: A boolean indicating whether the Order was called within a loop.
        first_loop_iteration: A boolean indicating whether the Order is called in the loop for the first time.
    """

    def __init__(
        self,
        order: Union[TransportOrder, MoveOrder, ActionOrder],
        task_context: TaskAPI,
        in_loop: bool,
    ):
        """Initialize the object.

        Args:
            order: The Order (TransportOrder, MoveOrder or Action) that is executed.
            task_context:  The corresponding Task(API) this Order is executed in.
            in_loop: A boolean indicating whether the Order was called within a loop.
        """
        self.uuid = str(uuid.uuid4())
        self.order: Union[TransportOrder, MoveOrder, ActionOrder] = order
        self.task_context: TaskAPI = task_context
        self.in_loop: bool = in_loop
        self.first_loop_iteration: bool = in_loop
