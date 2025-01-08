# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains Rule class."""

# standard libraries
from typing import Dict, List

# 3rd party libs
from antlr4.ParserRuleContext import ParserRuleContext


class Rule:
    """Represents a Rule in the MF-Plugin.

    Attributes:
        name: A string representing the name of the rule.
        parameters: A Dict which is mapping the parameter names to possible values.
        expressions: A list containing expressions defined in a Rule.
        context: ANTLR context object of this class.
    """

    def __init__(
        self,
        name: str = "",
        parameters: Dict = None,
        expressions: List[Dict] = None,
        context: ParserRuleContext = None,
    ) -> None:
        """Initialize the object.

        Args:
            name: A string representing the name of the rule.
            parameters: A Dict which is mapping the parameter names to possible values.
            expressions: A list containing expressions defined in a Rule.
            context: ANTLR context object of this class.
        """
        self.name: str = name

        self.parameters: Dict = {}
        if parameters:
            self.parameters = parameters

        self.expressions: List[Dict] = []
        if expressions:
            self.expressions = expressions

        self.context: ParserRuleContext = context
