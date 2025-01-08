# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains the OrderStepAPI class."""

# standard libraries
from typing import Union
import uuid

# local sources
## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order_step import TransportOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order_step import MoveOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order_step import ActionOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.api.order_api import OrderAPI


class OrderStepAPI:
    """Represents a started OrderStep.

    Represents a specific entity of a started OrderStep. This OrderStep is executed
    in the context of a specific running order (OrderAPI).

    Attributes.
        uuid: A UUID4 which is generated at object creation and is used in the scheduling.
        order_step: The OrderStep (TransportOrder, MoveOrder or Action OrderStep) that is executed.
        order_context: The corresponding Order(API) this OrderStep is executed in.
    """

    def __init__(
        self,
        order_step: Union[TransportOrderStep, MoveOrderStep, ActionOrderStep],
        order_context: OrderAPI,
    ):
        """Initialize the object.

        Args:
            order_step: The OrderStep (TransportOrder, MoveOrder or Action OrderStep) that is executed.
            order_context: The corresponding Order(API) this OrderStep is executed in.
        """
        self.uuid = str(uuid.uuid4())
        self.order_step: Union[TransportOrderStep, MoveOrderStep, ActionOrderStep] = order_step
        self.order_context: OrderAPI = order_context
