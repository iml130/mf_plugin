# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains helper functions used in the whole project."""

# standard libraries
from typing import Any, Dict, List, Tuple, Union

# local sources
## parent PFDL repo
from pfdl_scheduler.model.instance import Instance
from pfdl_scheduler.utils import helpers as pfdl_helpers

## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.rule import Rule
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.struct import Struct
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.process import Process


def substitute_parameter_in_expression(expression, subs: Dict) -> Union[str, Dict]:
    """Substitutes instance names with the values in subs.

    Returns:
        The expression with the substituted values.
    """
    # if the expression is only a string
    if isinstance(expression, str):
        if expression in subs:
            expression = subs[expression]
        return expression
    # attribute access
    if isinstance(expression, list):
        # the variable holds a single value
        instance_name = expression[0]
        if instance_name in subs:
            expression[0] = subs[instance_name]
        if len(expression) == 1:
            return expression[0]
        return expression
    if isinstance(expression, Tuple):
        # substitute only parameter names that are in the subs dict
        # while preserving the correct order of the parameters
        new_params = {}
        rule_name, rule_parameters = expression

        sub_list = list(subs)

        # substitute the parameters if possible and assign None to keep dict structure
        for rule_parameter in rule_parameters:
            if rule_parameter in sub_list:
                new_params[subs[rule_parameter]] = None
            else:
                new_params[rule_parameter] = None
        return (rule_name, new_params)
    if isinstance(expression, Dict):
        if len(expression) == 2:
            # the expression is a unary operation that contains a subexpression as value
            sub_expr = substitute_parameter_in_expression(expression["value"], subs)
            return {"unOp": expression["unOp"], "value": sub_expr}
        if expression["left"] == "(" and expression["right"] == ")":
            # the expression is a binary operation enclosed in brackets
            sub_expr = substitute_parameter_in_expression(expression["binOp"], subs)
            return {"left": "(", "binOp": sub_expr, "right": ")"}

        # binary operation with two subexpressions
        new_left = substitute_parameter_in_expression(expression["left"], subs)
        new_right = substitute_parameter_in_expression(expression["right"], subs)
        return {
            "left": new_left,
            "binOp": expression["binOp"],
            "right": new_right,
        }
    return expression


def get_attribute_access_value(
    attribute_access: List[str], instances: Dict[str, Instance]
) -> Union[int, float, bool, str]:
    """Get the exact value from a variable accessed through an attribute access.

    Args:
        attribute_access: The attribute access represented as a List of strings.
        instances: A Dict that contains all Instances of the PFDL program.

    Returns:
        The value (int, float, bool or str)
    """
    instance = instances[attribute_access[0]]
    value = None
    for i, attribute in enumerate(attribute_access[1:]):
        # last element in attribute list
        if i == len(attribute_access[1:]) - 1:
            value = instance.attributes[attribute]
        else:
            instance = instances[instance.attributes[attribute]]
    if isinstance(value, list):
        # the returned value is also an attribute access
        return get_attribute_access_value(value, instances)
    return value


def cast_element(element: Union[str, List]) -> Union[str, int, float, bool]:
    """
    Overwrites PFDL helper method to consider instances.

    Tries to cast the given string or list to a primitive datatype.

    Returns:
        The casted element if casting was successful, otherwise the input string
    """
    if isinstance(element, list) and len(element) == 1:

        return element[0]
    return pfdl_helpers.cast_element(element)


def evaluate_rule(rule_call: Tuple, instances: Dict[str, Instance], rules: Dict[str, Rule]) -> bool:
    """Executes the given Rule call with the help of Python expressions

    Args:
        rule_call: The given Rule call that should be evaluated.
        instances: A Dict that contains all Instances of the PFDL program.
        rules: A Dict that contains all Rules of the PFDL program.

    Returns:
        True if all expressions inside the values are evaluated as true.
    """
    rule_name = rule_call[0]
    rule_call_parameters = rule_call[1]
    rule = rules[rule_name]
    subs = {}

    # create a dict that maps parameter names of the rule to the passed values to the call
    if len(rule.parameters) > 0:
        for i, (rule_parameter, default_value) in enumerate(rule.parameters.items()):
            if i >= len(rule_call_parameters):
                subs[rule_parameter] = default_value
            else:
                subs[rule_parameter] = list(rule_call_parameters)[i]

    for expression in rule.expressions:
        substituted_expr = substitute_parameter_in_expression(expression, subs)
        if not execute_mf_plugin_expression(substituted_expr, instances, rules):
            return False
    return True


def execute_mf_plugin_expression(
    expression: Any, instances: Dict[str, Instance], rules: Dict[str, Rule]
) -> Any:
    """Executes the given PFDL expression as a Python expression.

    Args:
        expression: A dict representing the expression.
        instances: A Dict that contains all Instances of the PFDL program.
        rules: A Dict that contains all Rules of the PFDL program.

    Returns:
        The value of the expression executed in Python (type depends on specific expression).
    """
    if isinstance(expression, (int, float, bool)):
        return expression
    if isinstance(expression, str):
        # PFDL strings are saved with the '"" so delete it here
        if expression.startswith('"') and expression.endswith('"'):
            return expression.replace('"', "")
        return expression
    if isinstance(expression, List):
        value = get_attribute_access_value(expression, instances)
        if isinstance(value, str):
            value = value.replace('"', "")
        return value
    if isinstance(expression, Tuple):
        return evaluate_rule(expression, instances, rules)

    if isinstance(expression, Dict):
        if len(expression) == 2:
            return not execute_mf_plugin_expression(expression["value"], instances, rules)

        if expression["left"] == "(" and expression["right"] == ")":
            return execute_mf_plugin_expression(expression["binOp"], instances, rules)

        op_func = pfdl_helpers.parse_operator(expression["binOp"])

        try:
            # error handling because (due to multiple type declarations) it is possible
            # that the return types of the left and right expression are not compatible
            # e.g. int and string
            return op_func(
                execute_mf_plugin_expression(expression["left"], instances, rules),
                execute_mf_plugin_expression(expression["right"], instances, rules),
            )
        except TypeError as e:
            raise TypeError(
                "The given expression could not be validate because the types of the left and right side were not compatible!\n"
                + "TypeError with message: "
                + str((e))
            )


def add_primitive_structs(process: Process) -> None:
    """Adds the MF-Plugin primitives to the process structs."""
    process.structs["Location"] = Struct(
        "Location", {"id": "string", "time": "number", "type": "string"}
    )
    process.structs["Event"] = Struct(
        "Event", {"id": "string", "time": "number", "value": ["boolean", "number", "string"]}
    )
    process.structs["Time"] = Struct(
        "Time", {"id": "string", "time": "number", "timing": "string", "value": "boolean"}
    )
