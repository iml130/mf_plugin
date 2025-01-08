# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT


"""This class contains plugin code to overwrite the PFDL class Struct."""

# standard libraries
from typing import Dict, Union

# 3rd party libraries
from antlr4.ParserRuleContext import ParserRuleContext

# local sources
## PFDL base sources
import pfdl_scheduler
from pfdl_scheduler.model.array import Array
from pfdl_scheduler.plugins.plugin_loader import base_class


@base_class("Struct")
class Struct(pfdl_scheduler.model.struct.Struct):
    def __init__(
        self,
        name: str = "",
        attributes: Dict[str, Union[str, Array, "Struct"]] = None,
        parent_struct_name: str = "",
        context: ParserRuleContext = None,
    ) -> None:
        pfdl_scheduler.model.struct.Struct.__init__(
            self, name, attributes, context, parent_struct_name
        )

        # add attributes that exist in every struct by default
        self.attributes["id"] = "string"
        self.attributes["time"] = "number"
