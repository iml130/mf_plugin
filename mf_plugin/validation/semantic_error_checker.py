# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""This file contains plugin code to overwrite the PFDL class SemanticErrorChecker."""

# standard libraries
from typing import Dict, Tuple, Union, List, Any

# third party libraries
from antlr4.ParserRuleContext import ParserRuleContext

# local sources
## PFDL base sources
import pfdl_scheduler.plugins

from pfdl_scheduler.model.array import Array
from pfdl_scheduler.model.condition import Condition
from pfdl_scheduler.model.service import Service
from pfdl_scheduler.model.task_call import TaskCall
from pfdl_scheduler.model.counting_loop import CountingLoop
from pfdl_scheduler.model.while_loop import WhileLoop
from pfdl_scheduler.plugins.plugin_loader import base_class
import pfdl_scheduler.utils.helpers as pfdl_helpers

import pfdl_scheduler.validation.semantic_error_checker

## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.struct import Struct
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.task import Task
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order import ActionOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order_step import ActionOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order import MoveOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order_step import MoveOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.rule import Rule
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order import TransportOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order_step import TransportOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.process import Process

import pfdl_scheduler.plugins.mf_plugin.mf_plugin.helpers as mf_plugin_helpers

# Constants
ELEMENTARY_ATTRIBUTES = ["id", "time"]


@base_class("SemanticErrorChecker")
class SemanticErrorChecker(pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker):
    def validate_process(self) -> bool:
        """Overwrites the PFDL method to check MF-Plugin components too."""
        return (
            pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker.validate_process(
                self
            )
            & self.check_order_steps(self.process.transport_order_steps)
            & self.check_order_steps(self.process.move_order_steps)
            & self.check_order_steps(self.process.action_order_steps)
        )

    def check_statement(
        self,
        statement: Union[
            Service,
            TaskCall,
            WhileLoop,
            CountingLoop,
            Condition,
            TransportOrder,
            MoveOrder,
            ActionOrder,
        ],
        task: Task,
    ) -> bool:
        """Overwrites the PFDL method to ignore checking of orders."""

        # we do not need to check MF-Plugin statements (Orders) here, as they are already
        # checked while parsing
        if not isinstance(statement, (TransportOrder, MoveOrder, ActionOrder)):
            return pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker.check_statement(
                self, statement, task
            )
        return True

    def check_single_expression(
        self, expression: Union[str, list], context: ParserRuleContext, task: Task
    ) -> bool:
        """Checks if a single expression is a valid expression.
        Extends the PFDL method to enable multiple types for a variable.

        Returns:
            True if the given single expression is a valid expression.
        """
        if isinstance(expression, list):
            if not self.check_attribute_access(expression, context, task):
                return False
            # only numbers and booleans are allowed, so check the variable type
            variable_type = pfdl_helpers.get_type_of_variable_list(expression, task, self.structs)
            if isinstance(variable_type, list) and (
                "number" in variable_type or "boolean" in variable_type
            ):
                # multiple possible types, at least one is compatible
                return True

        # only a single value/type, run PFDL method
        return pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker.check_single_expression(
            self, expression, context, task
        )

    def expression_is_number(self, expression, task: Task) -> bool:
        """Checks if the given expression is a number (int or float).
        Extends the PFDL method to enable multiple types for a variable.

        Returns:
            True if the given expression is a number.
        """
        if isinstance(expression, list):
            given_type = pfdl_helpers.get_type_of_variable_list(expression, task, self.structs)
            if isinstance(given_type, list):
                # multiple possible types, check if number is included
                return "number" in given_type

        # only a single value/type, run PFDL method
        return pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker.expression_is_number(
            self, expression, task
        )

    def expression_is_string(self, expression, task: Task) -> bool:
        """Checks if the given expression is a PFDL string.
        Extends the PFDL method to enable multiple types for a variable.

        Returns:
            True if the given expression is a PFDL string.
        """
        if isinstance(expression, list):
            given_type = pfdl_helpers.get_type_of_variable_list(expression, task, self.structs)
            if isinstance(given_type, list):
                # multiple possible types, check if string is included
                return "string" in given_type

        # only a single value/type, run PFDL method
        return pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker.expression_is_string(
            self, expression, task
        )

    def check_if_variable_definition_is_valid(
        self, identifier: str, variable_type: Union[str, Array, List], context
    ) -> bool:
        """Checks if the variable has the correct type.
        Extends the PFDL method to enable multiple types for a variable.

        Returns:
            True if variable definition is valid.
        """
        if isinstance(variable_type, List):
            # multiple variable types defined
            for element_type in variable_type:
                if not self.check_if_variable_definition_is_valid(
                    identifier, element_type, context
                ):
                    return False
            return True
        else:
            # only a single value/type, run PFDL method
            return pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker.check_if_variable_definition_is_valid(
                self, identifier, variable_type, context
            )

    def check_type_of_value(self, value: Any, value_type: Union[str, list]) -> bool:
        """Checks if the given value is the given type in the DSL.
        Extends the PFDL method to enable multiple types for a variable.

        Returns:
            True if the value is from the given value type.
        """
        if isinstance(value_type, list):
            # multiple possible types, check if the given value is equal to one of them
            for type in value_type:
                if self.check_type_of_value(value, type):
                    return True
            return False

        # only a single value/type, run PFDL method
        if isinstance(value, list):
            # attribute access
            value = mf_plugin_helpers.get_attribute_access_value(value, self.process.instances)

        return pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker.check_type_of_value(
            self, value, value_type
        )

    def check_tasks(self) -> bool:
        """Executes semantic checks for all Tasks.

        Returns:
            True if the Task definition contains no static semantic errors."""

        # call pfdl task checks, returns True if no errors were found
        valid = pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker.check_tasks(
            self
        )

        for task in self.process.tasks.values():
            # execute MF-Plugin specific task checks
            if not (
                self.check_task_statements(task)
                & self.check_started_by(task)
                & self.check_finished_by(task)
                & self.check_constraints(task)
            ):
                valid = False
        return valid

    def check_task_statements(self, task: Task) -> bool:
        """Executes semantic checks for all statements in a Task
        (TransportOrder, MoveOrder and ActionOrder).

        Returns:
            True if all statements are valid.
        """
        if not len(task.statements):
            # no statements, happens when Task contains no active components (e.g. only StartedBy, Constraints, ...)
            error_msg = f"The Task {task.name} needs to contains at least one statement."
            self.error_handler.print_error(error_msg, context=task.context)
            return False
        for task_statement in task.statements:
            # check if a TransportOrder is called before any ActionOrder or MoveOrder
            if isinstance(task_statement, TransportOrder):
                # first TransportOrder is found before any ActionOrder or MoveOrder --> valid
                break
            elif isinstance(task_statement, (ActionOrder, MoveOrder)):
                error_msg = f"The Task {task.name} contains a Move or Action Order before a Transport Order was called."
                self.error_handler.print_error(error_msg, context=task.context)
                return False

        return True

    def check_started_by(
        self,
        task_or_order_step: Union[Task, TransportOrderStep, MoveOrderStep, ActionOrderStep],
    ) -> bool:
        """Checks if the StartedBy expression is valid.

        Returns:
            True if the StartedBy expression is valid.
        """
        expression = task_or_order_step.started_by_expr
        if expression is not None:
            return self.check_expression(
                expression, task_or_order_step.context_dict["StartedBy"], task_or_order_step
            )
        return True

    def check_finished_by(
        self,
        task_or_order_step: Union[Task, TransportOrderStep, MoveOrderStep, ActionOrderStep],
    ) -> bool:
        """Checks if the FinishedBy expression is valid.

        Returns:
            True if the FinishedBy expression is valid.
        """
        expression = task_or_order_step.finished_by_expr
        if expression is not None:
            return self.check_expression(
                expression, task_or_order_step.context_dict["FinishedBy"], task_or_order_step
            )
        return True

    def check_constraints(self, task: Task) -> bool:
        """Checks if the constraint is valid.

        Constraints can be a JSON object or an expression. If its a JSON object no further checks
        have to be executed, so just check if the constraint is an expression.

        Returns:
            True if the constraint is valid.
        """
        if isinstance(task.constraints, Dict):
            if not ("value" in task.constraints or "binOp" in task.constraints):
                # its a JSON object, will not be checked here
                return True
        return self.check_expression(task.constraints, task.context_dict["Constraints"], task)

    def check_expression(
        self, expression: Union[str, Tuple, Dict], context: ParserRuleContext, task: Task
    ) -> bool:
        """Executes checks for the given expression.

        Returns:
            True if the given expression is valid.
        """

        # a dummy task has to be created and filled with the instances as variables in order
        # for the PFDL validation to not crash
        dummy_task = Task()
        if isinstance(task, Task) and task.variables:
            dummy_task.variables = task.variables
        else:
            for instance in self.process.instances.values():
                dummy_task.variables[instance.name] = instance.struct_name

        # A Rule call is always a boolean expression so check if the rule call
        # itself is valid with the given parameters
        if isinstance(expression, Tuple):
            return self.check_rule_call(expression, dummy_task, context)

        return (
            pfdl_scheduler.validation.semantic_error_checker.SemanticErrorChecker.check_expression(
                self, expression, context, dummy_task
            )
        )

    def check_rule_call(
        self,
        rule_call: Tuple,
        task: Task,
        context: ParserRuleContext = None,
    ) -> bool:
        """Executes semantic checks for a Rule call.

        A Rule call can be used inside a Rule definiton or inside
        Tasks and OrderSteps (e.g. with StartedBy or FinishedBy).
        If parameters are used, substitute the parameters inside the corresponding
        Rule definition with the real values and check the expressions then.

        Returns:
            True if the Rule call is valid.
        """
        rule_name, rule_call_parameters = rule_call

        # check if rule exists
        if not rule_name in self.process.rules:
            error_msg = f"Rulecall '{rule_name}' refers to an unknown Rule."
            self.error_handler.print_error(error_msg, context=context)
            return False

        valid = True

        rule = self.process.rules[rule_name]
        parameter_substitutions = {}  # mapping of the parameters to actual values in rule call
        # substitute each rule parameter with its actual value in the rule call
        for rule_call_parameter, rule_parameter in zip(
            rule_call_parameters.keys(), rule.parameters.keys()
        ):
            parameter_substitutions[rule_parameter] = rule_call_parameter

        if len(rule.parameters) > len(rule_call_parameters):
            # not all parameters of the rule where initialized in the rule call, use default value for those
            for rule_call_parameter, default_value in list(rule.parameters.items())[
                len(rule_call_parameters) :
            ]:
                if default_value is not None:
                    parameter_substitutions[rule_call_parameter] = pfdl_helpers.cast_element(
                        default_value
                    )
                else:
                    error_msg = f"Neither default value nor value for parameter '{rule_call_parameter}' was provided."
                    self.error_handler.print_error(error_msg, context=context)
                    valid = False

        for expression in rule.expressions:
            test_expression = expression
            if parameter_substitutions:
                test_expression = mf_plugin_helpers.substitute_parameter_in_expression(
                    expression, parameter_substitutions
                )
            if not self.check_expression(test_expression, context, task):
                valid = False
        return valid

    def check_order_steps(
        self, order_steps: Dict[str, Union[TransportOrderStep, MoveOrderStep, ActionOrderStep]]
    ) -> bool:
        """Executes checks for all OrderSteps in the given dict.

        Returns:
            True if all OrderSteps are valid.
        """
        valid = True
        for order_step in order_steps.values():
            if not (
                self.check_on_done(order_step)
                & self.check_started_by(order_step)
                & self.check_finished_by(order_step)
            ):
                valid = False
        return valid

    def check_on_done(
        self, order_step: Union[TransportOrderStep, MoveOrderStep, ActionOrderStep]
    ) -> bool:
        """Checks if the task in OnDone refers to a known task.

        Returns:
            True if the task in OnDone refers to a known task.
        """
        valid = True

        if order_step.follow_up_task_name != "":
            # OrderStep contains an OnDone task
            if order_step.follow_up_task_name not in self.tasks:
                error_msg = (
                    f"The task name '{order_step.follow_up_task_name}' in the OnDone statement refers "
                    f"to an unknown Task."
                )
                self.error_handler.print_error(error_msg, context=order_step.context)
                valid = False
        return valid
