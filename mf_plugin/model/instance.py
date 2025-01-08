# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

from typing import Dict, Union
import uuid

from antlr4 import ParserRuleContext

import pfdl_scheduler
from pfdl_scheduler.model.struct import Struct
from pfdl_scheduler.pfdl_base_classes import PFDLBaseClasses
from pfdl_scheduler.plugins.plugin_loader import base_class
from pfdl_scheduler.validation.error_handler import ErrorHandler


@base_class("Instance")
class Instance(pfdl_scheduler.model.instance.Instance):
    @classmethod
    def from_json(
        cls,
        json_object: Dict,
        error_handler: ErrorHandler,
        struct_context: ParserRuleContext,
        pfdl_base_classes: PFDLBaseClasses,
    ):
        return cls.parse_json(json_object, error_handler, struct_context, pfdl_base_classes)

    @classmethod
    def parse_json(
        cls,
        json_object: Dict,
        error_handler: ErrorHandler,
        instance_context: ParserRuleContext,
        pfdl_base_classes: PFDLBaseClasses,
    ) -> "Instance":
        instance = pfdl_scheduler.model.instance.parse_json(
            json_object, error_handler, instance_context, pfdl_base_classes
        )

        return cls.add_standard_struct_attributes(instance)

    @classmethod
    def add_standard_struct_attributes(
        cls, instance: Union[Struct, "Instance"]
    ) -> Union[Struct, "Instance"]:
        """
        Set default values for attributes that exists in every struct (if they were not set already).
        """

        # Add default attributes to the current instance
        if "time" not in instance.attributes:
            instance.attributes["time"] = 0
        if "id" not in instance.attributes:
            instance.attributes["id"] = str(uuid.uuid4())

        # Recursively check and apply defaults to any nested instances
        for attribute_name, attribute_value in instance.attributes.items():
            if attribute_value.__class__.__name__ == "Instance":
                # Recursively apply defaults to nested instances
                instance.attributes[attribute_name] = cls.add_standard_struct_attributes(
                    attribute_value
                )

        return instance
