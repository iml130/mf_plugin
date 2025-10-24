# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains TransportOrder class."""

# standard libraries
from typing import List
from uuid import uuid4

# 3rd party libs
from antlr4.ParserRuleContext import ParserRuleContext

# local sources
## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order_step import TransportOrderStep


class TransportOrder:
    """Represents a TransportOrder (Transport statement) in the MF-Plugin.

    Attributes:
        pickup_tos_names: A List of strings representing the name of the TransportOrderSteps.
        pickup_tos: A List of TransportOrderSteps in the 'From' statement.
        delivery_tos_names: A List of strings representing the name of the TransportOrderSteps in the 'To' statement.
        delivery_tos: A List of TransportOrderSteps in the 'To' statement.
        context: ANTLR context object of this class.
    """

    def __init__(
        self,
        pickup_tos_names: List[str] = None,
        pickup_tos: List[TransportOrderStep] = None,
        delivery_tos_names: List[str] = None,
        delivery_tos: List[TransportOrderStep] = None,
        context: ParserRuleContext = None,
    ) -> None:
        """Initialize the object.

        Args:
            pickup_tos_names: A List of strings representing the name of the TransportOrderSteps.
            pickup_tos: A List of TransportOrderSteps in the 'From' statement.
            delivery_tos_names: A List of strings representing the name of the TransportOrderSteps in the 'To' statement.
            delivery_tos: A List of TransportOrderSteps in the 'To' statement.
            context: ANTLR context object of this class.
        """
        self.pickup_tos_names: List[str] = []
        if pickup_tos_names:
            self.pickup_tos_names = pickup_tos_names

        self.pickup_tos: List[TransportOrderStep] = []
        if pickup_tos:
            self.pickup_tos = pickup_tos

        self.delivery_tos_names: List[str] = []
        if delivery_tos_names:
            self.delivery_tos_names = delivery_tos_names

        self.delivery_tos: List[TransportOrderStep] = []
        if delivery_tos:
            self.delivery_tos = delivery_tos

        self.context: ParserRuleContext = context
