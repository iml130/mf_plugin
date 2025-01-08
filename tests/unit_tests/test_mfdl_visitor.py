# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains unit tests for the self.mf_plugin_visitor.

The Testself.mf_plugin_visitor class contains unit tests which tests each method of the
self.mf_plugin_visitor class. A syntax tree with every language component in it is build up
from a PFDL program in the setUp method for testing the Visitor methods.
"""

# standard libraries
from typing import Dict
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

# 3rd party
from antlr4.Token import Token
from antlr4 import ParserRuleContext
from antlr4.tree.Tree import TerminalNodeImpl


# local sources
## PFDL base sources
import pfdl_scheduler
from pfdl_scheduler.model.array import Array
from pfdl_scheduler.model.instance import Instance
from pfdl_scheduler.pfdl_base_classes import PFDLBaseClasses
from pfdl_scheduler.plugins.plugin_loader import PluginLoader
from pfdl_scheduler.validation.error_handler import ErrorHandler
from pfdl_scheduler.model.condition import Condition
from pfdl_scheduler.model.while_loop import WhileLoop
from pfdl_scheduler.model.counting_loop import CountingLoop

## important for unit tests to work
from pfdl_scheduler.model.struct import Struct as StructPFDL
from pfdl_scheduler.model.task import Task as TaskPFDL

## MF-Plugin sources

from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.process import Process
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.struct import Struct
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.rule import Rule
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.task import Task
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order import TransportOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order import MoveOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order_step import MoveOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order import ActionOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order_step import TransportOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order_step import ActionOrderStep
from pfdl_scheduler.plugins.parser.PFDLParser import PFDLParser
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.parser.pfdl_tree_visitor import PFDLTreeVisitor

plugin_loader = PluginLoader()
plugin_loader.load_plugins(["mf_plugin/mf_plugin"])
pfdl_base_classes = plugin_loader.get_pfdl_base_classes()


class TestPFDLTreeVisitor(unittest.TestCase):
    """Testcase containing unit tests for the self.mf_plugin_visitor.

    Attributes:
        mf_plugin_visitor: A self.mf_plugin_visitor object which contains the methods who should be tested.
    """

    def setUp(self) -> None:
        self.mf_plugin_visitor = PFDLTreeVisitor(ErrorHandler("", False), pfdl_base_classes)

    def assert_print_error_is_called(self, method, *args) -> None:
        """Runs the given method with the help of a mock object and checks if print error is called.

        Args:
            method: The method which should be tested.
            args: Variable amount of arguments for the method to be tested.
        """
        with patch.object(self.mf_plugin_visitor.error_handler, "print_error") as mock:
            method(*args)
        mock.assert_called()

    def test_visitProgram(self):
        """Checks if a PFDL program with MF-Plugin components is returned and
        all components are in the different dicts."""
        mf_plugin_program = None

        program_context = PFDLParser.ProgramContext(None)
        program_context.children = [
            PFDLParser.StructContext(None),
            PFDLParser.StructContext(None),
            PFDLParser.StructContext(None),
        ]
        with patch.object(
            self.mf_plugin_visitor,
            "visitStruct",
            MagicMock(
                side_effect=[
                    Struct(name="struct_1"),
                    Struct(name="struct_1"),
                    Struct(name="struct_2"),
                ]
            ),
        ):
            mf_plugin_program = self.mf_plugin_visitor.visitProgram(program_context)

        self.assertIsNotNone(mf_plugin_program)

        # 3 primitives (Location, Time and Event) + the 2 structs
        self.assertEqual(len(mf_plugin_program.structs), 5)

        program_context.children = [
            PFDLParser.InstanceContext(None),
            PFDLParser.InstanceContext(None),
            PFDLParser.InstanceContext(None),
        ]

        with patch.object(
            self.mf_plugin_visitor,
            "visitInstance",
            MagicMock(
                side_effect=[
                    Instance(name="instance_1"),
                    Instance(name="instance_1"),
                    Instance(name="instance_2"),
                ]
            ),
        ):
            mf_plugin_program = self.mf_plugin_visitor.visitProgram(program_context)

        self.assertIsNotNone(mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.instances), 2)

        program_context.children = [
            PFDLParser.Rule_Context(None),
            PFDLParser.Rule_Context(None),
            PFDLParser.Rule_Context(None),
        ]

        with patch.object(
            self.mf_plugin_visitor,
            "visitRule_",
            MagicMock(
                side_effect=[
                    Rule(name="rule_1"),
                    Rule(name="rule_1"),
                    Rule(name="rule_2"),
                ]
            ),
        ):
            mf_plugin_program = self.mf_plugin_visitor.visitProgram(program_context)

        self.assertIsNotNone(mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.rules), 2)

        program_context.children = [
            PFDLParser.TaskContext(None),
            PFDLParser.TaskContext(None),
            PFDLParser.TaskContext(None),
        ]

        with patch.object(
            self.mf_plugin_visitor,
            "visitTask",
            MagicMock(
                side_effect=[
                    Task(name="task_1"),
                    Task(name="task_1"),
                    Task(name="task_2"),
                ]
            ),
        ):
            mf_plugin_program = self.mf_plugin_visitor.visitProgram(program_context)

        self.assertIsNotNone(mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.tasks), 2)

        program_context.children = [
            PFDLParser.TransportOrderStepContext(None),
            PFDLParser.TransportOrderStepContext(None),
            PFDLParser.TransportOrderStepContext(None),
        ]

        with patch.object(
            self.mf_plugin_visitor,
            "visitTransportOrderStep",
            MagicMock(
                side_effect=[
                    TransportOrderStep(name="tos1"),
                    TransportOrderStep(name="tos1"),
                    TransportOrderStep(name="tos2"),
                ]
            ),
        ):
            mf_plugin_program = self.mf_plugin_visitor.visitProgram(program_context)

        self.assertIsNotNone(mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.transport_order_steps), 2)

        program_context.children = [
            PFDLParser.ActionOrderStepContext(None),
            PFDLParser.ActionOrderStepContext(None),
            PFDLParser.ActionOrderStepContext(None),
        ]

        with patch.object(
            self.mf_plugin_visitor,
            "visitActionOrderStep",
            MagicMock(
                side_effect=[
                    ActionOrderStep(name="aos_1"),
                    ActionOrderStep(name="aos_1"),
                    ActionOrderStep(name="aos_2"),
                ]
            ),
        ):
            mf_plugin_program = self.mf_plugin_visitor.visitProgram(program_context)

    def test_process_mf_plugin_component(self):
        mf_plugin_program = Process()
        struct = Struct("struct_id")

        self.mf_plugin_visitor.process_mf_plugin_component(struct, mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.structs), 1)
        self.assertEqual(mf_plugin_program.structs["struct_id"], struct)

        # equal attributes should cause an error
        self.assert_print_error_is_called(
            self.mf_plugin_visitor.process_mf_plugin_component, struct, mf_plugin_program
        )

        task = Task("task_id")

        self.mf_plugin_visitor.process_mf_plugin_component(task, mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.tasks), 1)
        self.assertEqual(mf_plugin_program.tasks["task_id"], task)

        instance = Instance("instance_id")

        self.mf_plugin_visitor.process_mf_plugin_component(instance, mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.instances), 1)
        self.assertEqual(mf_plugin_program.instances["instance_id"], instance)

        rule = Rule("rule_id")

        self.mf_plugin_visitor.process_mf_plugin_component(rule, mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.rules), 1)
        self.assertEqual(mf_plugin_program.rules["rule_id"], rule)

        tos = TransportOrderStep("tos_id")

        self.mf_plugin_visitor.process_mf_plugin_component(tos, mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.transport_order_steps), 1)
        self.assertEqual(mf_plugin_program.transport_order_steps["tos_id"], tos)

        mos = MoveOrderStep("mos_id")

        self.mf_plugin_visitor.process_mf_plugin_component(mos, mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.move_order_steps), 1)
        self.assertEqual(mf_plugin_program.move_order_steps["mos_id"], mos)

        aos = ActionOrderStep("aos_id")

        self.mf_plugin_visitor.process_mf_plugin_component(aos, mf_plugin_program)
        self.assertEqual(len(mf_plugin_program.action_order_steps), 1)
        self.assertEqual(mf_plugin_program.action_order_steps["aos_id"], aos)

    def test_visitRule_(self):
        rule_context = PFDLParser.Rule_Context(None)
        rule_context.children = [
            PFDLParser.Rule_callContext(None),
            PFDLParser.ExpressionContext(None),
            PFDLParser.ExpressionContext(None),
        ]

        rule_call = ("rule_name", {"arg_1": "5", "arg_2": "str"})
        expression_1 = {"unOp": "!", "value": "event.a_bool"}
        expression_2 = {"left": "event.an_int", "binOp": "==", "right": 10}

        with patch.object(
            self.mf_plugin_visitor,
            "visitRule_call",
            MagicMock(side_effect=[rule_call]),
        ):
            with patch.object(
                self.mf_plugin_visitor,
                "visitExpression",
                MagicMock(side_effect=[expression_1, expression_2]),
            ):
                rule = self.mf_plugin_visitor.visitRule_(rule_context)

        self.assertEqual(rule.name, "rule_name")
        self.assertEqual(len(rule.parameters), 2)
        self.assertTrue("arg_1" in rule.parameters)
        self.assertTrue("arg_2" in rule.parameters)
        self.assertEqual(rule.parameters["arg_1"], "5")
        self.assertEqual(rule.parameters["arg_2"], "str")
        self.assertEqual(len(rule.expressions), 2)
        self.assertEqual(len(rule.expressions[0]), 2)
        self.assertEqual(len(rule.expressions[1]), 3)
        self.assertEqual(rule.expressions[0]["unOp"], "!")
        self.assertEqual(rule.expressions[0]["value"], "event.a_bool")
        self.assertEqual(rule.expressions[1]["left"], "event.an_int")
        self.assertEqual(rule.expressions[1]["binOp"], "==")
        self.assertEqual(rule.expressions[1]["right"], 10)

    def test_visitRule_call(self):
        rule_call_context = PFDLParser.Rule_callContext(None)

        rule_call_context.children = [PFDLParser.Rule_parameterContext(None)]
        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "rule_id", rule_call_context)

        with patch.object(
            self.mf_plugin_visitor,
            "visitRule_parameter",
            MagicMock(side_effect=[("arg", "False")]),
        ):
            rule_id, parameters = self.mf_plugin_visitor.visitRule_call(rule_call_context)

        self.assertEqual(rule_id, "rule_id")
        self.assertEqual(len(parameters), 1)
        self.assertTrue("arg" in parameters)
        self.assertEqual(parameters["arg"], "False")

        # multiple parameters
        rule_call_context.children = [
            PFDLParser.Rule_parameterContext(None),
            PFDLParser.Rule_parameterContext(None),
            PFDLParser.Rule_parameterContext(None),
        ]
        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "rule_id", rule_call_context)

        with patch.object(
            self.mf_plugin_visitor,
            "visitRule_parameter",
            MagicMock(side_effect=[("arg", "5"), ("bool", "True"), ("float", "5.0")]),
        ):
            rule_id, parameters = self.mf_plugin_visitor.visitRule_call(rule_call_context)

        self.assertEqual(rule_id, "rule_id")
        self.assertEqual(len(parameters), 3)
        self.assertTrue("arg" in parameters)
        self.assertEqual(parameters["arg"], "5")
        self.assertTrue("bool" in parameters)
        self.assertEqual(parameters["bool"], "True")
        self.assertTrue("float" in parameters)
        self.assertEqual(parameters["float"], "5.0")

        # duplicate parameters, should cause an error
        rule_call_context.children = [
            PFDLParser.Rule_parameterContext(None),
            PFDLParser.Rule_parameterContext(None),
        ]
        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "rule_id", rule_call_context)

        with patch.object(
            self.mf_plugin_visitor,
            "visitRule_parameter",
            MagicMock(side_effect=[("arg", "5"), ("arg", "3")]),
        ):
            self.assert_print_error_is_called(
                self.mf_plugin_visitor.visitRule_call, rule_call_context
            )

    def test_visitRule_parameter(self):
        rule_parameter_context = PFDLParser.Rule_parameterContext(None)
        rule_parameter_context.children = [PFDLParser.ValueContext(None)]

        arg = value = ""
        # used as rule definition parameters
        with patch.object(
            self.mf_plugin_visitor,
            "visitValue",
            MagicMock(side_effect=["arg"]),
        ):
            arg, value = self.mf_plugin_visitor.visitRule_parameter(rule_parameter_context)

        self.assertEqual(arg, "arg")
        self.assertEqual(value, None)

        arg = value = ""

        rule_parameter_context = PFDLParser.Rule_parameterContext(None)
        rule_parameter_context.children = [PFDLParser.ValueContext(None)]
        create_and_add_token(PFDLParser.EQUAL, "=", rule_parameter_context)
        rule_parameter_context.children.append(PFDLParser.ValueContext(None))

        with patch.object(
            self.mf_plugin_visitor,
            "visitValue",
            MagicMock(side_effect=["arg", 5]),
        ):
            arg, value = self.mf_plugin_visitor.visitRule_parameter(rule_parameter_context)

        self.assertEqual(arg, "arg")
        self.assertEqual(value, 5)

        arg = value = ""
        # used as parameters in a rule call
        rule_parameter_context = PFDLParser.Rule_parameterContext(None)
        rule_parameter_context.children = [PFDLParser.ValueContext(None)]
        create_and_add_token(PFDLParser.EQUAL, "=", rule_parameter_context)
        rule_parameter_context.children.append(PFDLParser.ValueContext(None))

        with patch.object(
            self.mf_plugin_visitor,
            "visitValue",
            MagicMock(side_effect=["True", 5.0]),
        ):
            arg, value = self.mf_plugin_visitor.visitRule_parameter(rule_parameter_context)

        self.assertEqual(arg, "True")
        self.assertEqual(value, 5.0)

    def test_visitTask(self):
        task_context = PFDLParser.TaskContext(None)
        task_statement_context = PFDLParser.TaskStatementContext(None)
        task_context.children = [task_statement_context]

        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "task_id", task_context)

        with patch.object(self.mf_plugin_visitor, "visitTaskStatement", return_value=None) as mock:
            task = self.mf_plugin_visitor.visitTask(task_context)

        mock.assert_called_with(task_statement_context, task)
        self.assertIsNotNone(task)
        self.assertEqual(task.name, "task_id")

        # task in
        task_context.children = [PFDLParser.Task_inContext(None)]

        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "task_id", task_context)

        with patch.object(
            self.mf_plugin_visitor, "visitTask_in", return_value={"attr": ""}
        ) as mock:
            with patch.object(self.mf_plugin_visitor, "visitTaskStatement", return_value=None):
                task = self.mf_plugin_visitor.visitTask(task_context)

        self.assertEqual(task.name, "task_id")
        self.assertEqual(len(task.input_parameters), 1)

        # task out
        task_context.children = [PFDLParser.Task_outContext(None)]

        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "task_id", task_context)

        with patch.object(
            self.mf_plugin_visitor, "visitTask_out", return_value={"attr": ""}
        ) as mock:
            with patch.object(self.mf_plugin_visitor, "visitTaskStatement", return_value=None):
                task = self.mf_plugin_visitor.visitTask(task_context)

        self.assertEqual(task.name, "task_id")
        self.assertEqual(len(task.output_parameters), 1)

    def test_visitTaskStatement(self):
        task_statement_context = PFDLParser.TaskStatementContext(None)
        current_task = Task()
        self.mf_plugin_visitor.current_program_component = current_task

        statement_context = PFDLParser.StatementContext(None)

        task_statement_context.children = [statement_context]
        statement_context.children = [PFDLParser.TransportStatementContext(None)]
        transport_order = TransportOrder()
        with patch.object(
            self.mf_plugin_visitor,
            "visitStatement",
            MagicMock(side_effect=[transport_order]),
        ) as visitStatementMock:
            self.mf_plugin_visitor.visitTaskStatement(task_statement_context, current_task)

        visitStatementMock.assert_called_with(statement_context)
        self.assertEqual(len(current_task.statements), 1)
        self.assertEqual(current_task.statements[0], transport_order)

        # test event statement
        event_statement_context = PFDLParser.EventStatementContext(None)

        task_statement_context.children = [event_statement_context]
        with patch.object(
            self.mf_plugin_visitor, "process_event_statement", MagicMock(side_effect=[None])
        ) as processEventStatementMock:
            self.mf_plugin_visitor.visitTaskStatement(task_statement_context, current_task)

        processEventStatementMock.assert_called_once_with(task_statement_context, current_task)

        # test Constraint
        constraint_statement_context = PFDLParser.ConstraintStatementContext(None)

        task_statement_context.children = [constraint_statement_context]

        constraint = {"number_of_packages": 10}
        constraint_string = '{"number_of_packages": 10}'
        with patch.object(
            self.mf_plugin_visitor,
            "visitConstraintStatement",
            MagicMock(side_effect=[(constraint, constraint_string)]),
        ):
            self.mf_plugin_visitor.visitTaskStatement(task_statement_context, current_task)

        self.assertEqual(len(current_task.constraints), 1)
        self.assertEqual(current_task.constraints, constraint)
        self.assertEqual(current_task.constraints_string, constraint_string)
        self.assertEqual(current_task.context_dict["Constraints"], constraint_statement_context)

        # try to add another Constraint statement (should raise an error)
        constraint_statement_context_2 = PFDLParser.ConstraintStatementContext(None)
        task_statement_context.children = [constraint_statement_context_2]

        constraint_2 = {"number_of_packages": 20}
        constraint_string_2 = '{"number_of_packages": 20}'
        with patch.object(
            self.mf_plugin_visitor,
            "visitConstraintStatement",
            MagicMock(side_effect=[(constraint_2, constraint_string_2)]),
        ) as constraintStatementMock:
            self.assert_print_error_is_called(
                self.mf_plugin_visitor.visitTaskStatement, task_statement_context, current_task
            )
        self.assertEqual(constraintStatementMock.call_count, 0)

        # assert the task was not changed by the second constraint
        self.assertEqual(len(current_task.constraints), 1)
        self.assertEqual(current_task.constraints, constraint)
        self.assertEqual(current_task.constraints_string, constraint_string)
        self.assertEqual(current_task.context_dict["Constraints"], constraint_statement_context)

    def test_visitStatement(self):
        task_stmt_context = PFDLParser.StatementContext(None)
        current_task = Task()
        self.mf_plugin_visitor.current_program_component = current_task

        task_stmt_context.children = [PFDLParser.TransportStatementContext(None)]
        transport_order = TransportOrder()
        with patch.object(
            self.mf_plugin_visitor,
            "visitTransportStatement",
            MagicMock(side_effect=[transport_order]),
        ):
            statement = self.mf_plugin_visitor.visitStatement(task_stmt_context)

        self.assertIsNotNone(statement)
        self.assertEqual(statement, transport_order)

        task_stmt_context.children = [PFDLParser.MoveStatementContext(None)]
        move_order = MoveOrder()
        with patch.object(
            self.mf_plugin_visitor,
            "visitMoveStatement",
            MagicMock(side_effect=[move_order]),
        ):
            statement = self.mf_plugin_visitor.visitStatement(task_stmt_context)

        self.assertIsNotNone(statement)
        self.assertEqual(statement, move_order)

        task_stmt_context.children = [PFDLParser.ActionStatementContext(None)]
        action_order = ActionOrder()
        with patch.object(
            self.mf_plugin_visitor,
            "visitActionStatement",
            MagicMock(side_effect=[action_order]),
        ):
            statement = self.mf_plugin_visitor.visitStatement(task_stmt_context)

        self.assertIsNotNone(statement)
        self.assertEqual(statement, action_order)

    def test_visitTransportStatement(self):
        transport_stmt_context = PFDLParser.TransportStatementContext(None)
        transport_stmt_context.children = [
            PFDLParser.TosCollectionStatementContext(None),
            PFDLParser.TosCollectionStatementContext(None),
        ]

        pickup_tos = ["tos1", "tos2"]
        delivery_tos = ["tos3", "tos4"]
        with patch.object(
            self.mf_plugin_visitor,
            "visitTosCollectionStatement",
            MagicMock(side_effect=[pickup_tos, delivery_tos]),
        ):
            transport_order = self.mf_plugin_visitor.visitTransportStatement(transport_stmt_context)
        self.assertEqual(transport_order.pickup_tos_names, pickup_tos)
        self.assertEqual(transport_order.delivery_tos_names, delivery_tos)

    def visitTosCollectionStatement(self):
        tos_collection_stmt_context = PFDLParser.TosCollectionStatementContext(None)
        create_and_add_token(
            PFDLParser.STARTS_WITH_LOWER_C_STR, "tos1", tos_collection_stmt_context
        )
        create_and_add_token(
            PFDLParser.STARTS_WITH_LOWER_C_STR, "tos2", tos_collection_stmt_context
        )
        create_and_add_token(
            PFDLParser.STARTS_WITH_LOWER_C_STR, "tos3", tos_collection_stmt_context
        )
        tos_names = self.mf_plugin_visitor.visitFromStatement(tos_collection_stmt_context)
        self.assertEqual(len(tos_names), 3)
        self.assertEqual(tos_names[0], "tos1")
        self.assertEqual(tos_names[1], "tos2")
        self.assertEqual(tos_names[2], "tos3")

    def test_visitMoveStatement(self):
        move_stmt_context = PFDLParser.MoveStatementContext(None)
        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "tos_id", move_stmt_context)
        move_order = self.mf_plugin_visitor.visitMoveStatement(move_stmt_context)
        self.assertEqual(move_order.move_order_step_name, "tos_id")

    def test_visitActionStatement(self):
        action_stmt_context = PFDLParser.ActionStatementContext(None)
        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "aos_id", action_stmt_context)
        action_order = self.mf_plugin_visitor.visitActionStatement(action_stmt_context)
        self.assertEqual(action_order.action_order_step_name, "aos_id")

    def test_visitConstraintStatement(self):
        constraint_stmt_context = PFDLParser.ConstraintStatementContext(None)
        constraint_stmt_context.children = [PFDLParser.ExpressionContext(None)]

        current_task = Task()
        self.mf_plugin_visitor.current_program_component = current_task

        expression = {"unOp": "!", "value": "True"}
        json_object = {"name": "John", "age": 30, "city": "New York"}

        with patch.object(
            self.mf_plugin_visitor,
            "visitExpression",
            MagicMock(side_effect=[expression]),
        ):
            constraint, constraint_string = self.mf_plugin_visitor.visitConstraintStatement(
                constraint_stmt_context
            )

        self.assertEqual(constraint, expression)

        constraint_stmt_context.children = [PFDLParser.Json_objectContext(None)]

        with patch.object(
            self.mf_plugin_visitor,
            "visitJson_object",
            MagicMock(side_effect=[json_object]),
        ):
            constraint, constraint_string = self.mf_plugin_visitor.visitConstraintStatement(
                constraint_stmt_context
            )

        self.assertEqual(constraint, json_object)

    def test_visitEventStatement(self):
        event_stmt_context = PFDLParser.EventStatementContext(None)
        event_stmt_context.children = [PFDLParser.ExpressionContext(None)]

        mock_expression = {"left": "event.an_int", "binOp": "==", "right": 10}
        with patch.object(
            self.mf_plugin_visitor,
            "visitExpression",
            MagicMock(side_effect=[mock_expression]),
        ):
            expression = self.mf_plugin_visitor.visitEventStatement(event_stmt_context)

        self.assertEqual(expression, mock_expression)

    def test_visitExpression(self):
        expression_context = PFDLParser.ExpressionContext(None)
        mock_expression = {"left": "event.an_int", "binOp": "==", "right": 10}

        with patch.object(
            pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor,
            "visitExpression",
            MagicMock(side_effect=[mock_expression]),
        ):
            expression = self.mf_plugin_visitor.visitExpression(expression_context)

        self.assertEqual(expression, mock_expression)

        rule_call_context = PFDLParser.Rule_callContext(None)
        expression_context.children = [rule_call_context]

        mock_expression = ["event1", {"event2": None}]

        with patch.object(
            pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor,
            "visitExpression",
            MagicMock(side_effect=[None]),
        ):
            with patch.object(
                pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor,
                "get_content",
                MagicMock(side_effect=[mock_expression]),
            ):
                expression = self.mf_plugin_visitor.visitExpression(expression_context)

        self.assertEqual(expression, mock_expression)

    def test_visitOrderStep(self):
        # TransportOrderStep
        order_step_context = PFDLParser.OrderStepContext(None)
        order_step_context.children = [PFDLParser.TransportOrderStepContext(None)]
        with patch.object(
            self.mf_plugin_visitor,
            "visitTransportOrderStep",
            MagicMock(side_effect=[TransportOrderStep(name="tos_name")]),
        ):
            transport_order_step = self.mf_plugin_visitor.visitOrderStep(order_step_context)

        self.assertTrue(isinstance(transport_order_step, TransportOrderStep))
        self.assertEqual(transport_order_step.name, "tos_name")

        # MoveOrderStep
        order_step_context.children = [PFDLParser.MoveOrderStepContext(None)]
        with patch.object(
            self.mf_plugin_visitor,
            "visitMoveOrderStep",
            MagicMock(side_effect=[MoveOrderStep(name="mos_name")]),
        ):
            move_order_step = self.mf_plugin_visitor.visitOrderStep(order_step_context)
        self.assertTrue(isinstance(move_order_step, MoveOrderStep))
        self.assertEqual(move_order_step.name, "mos_name")

        # ActionOrderStep
        order_step_context.children = [PFDLParser.ActionOrderStepContext(None)]
        with patch.object(
            self.mf_plugin_visitor,
            "visitActionOrderStep",
            MagicMock(side_effect=[ActionOrderStep(name="aos_name")]),
        ):
            action_order_step = self.mf_plugin_visitor.visitOrderStep(order_step_context)
        self.assertTrue(isinstance(action_order_step, ActionOrderStep))
        self.assertEqual(action_order_step.name, "aos_name")

    def test_visitTransportOrderStep(self):
        transport_order_step_context = PFDLParser.TransportOrderStepContext(None)

        transport_order_step_context.children = [
            PFDLParser.TosStatementContext(None),
            PFDLParser.TosStatementContext(None),
        ]
        create_and_add_token(
            PFDLParser.STARTS_WITH_LOWER_C_STR, "tos_id", transport_order_step_context
        )

        # check if tosstatement method is called
        with patch.object(self.mf_plugin_visitor, "visitTosStatement", return_value=None) as mock:
            transport_order_step = self.mf_plugin_visitor.visitTransportOrderStep(
                transport_order_step_context
            )

        self.assertEqual(mock.call_count, 2)
        self.assertIsNotNone(transport_order_step)
        self.assertEqual(transport_order_step.name, "tos_id")
        self.assertEqual(transport_order_step.context, transport_order_step_context)
        self.assertEqual(self.mf_plugin_visitor.current_program_component, transport_order_step)

    def test_visitTosStatement(self):
        # test Location statement
        tos_statement_context = PFDLParser.TosStatementContext(None)
        tos_statement_context.children = [PFDLParser.LocationStatementContext(None)]

        current_tos = TransportOrderStep()
        with patch.object(
            self.mf_plugin_visitor,
            "process_location_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitTosStatement(tos_statement_context, current_tos)

        mock.assert_called_once()

        # test Parameter statement
        tos_statement_context.children = [PFDLParser.ParameterStatementContext(None)]
        with patch.object(
            self.mf_plugin_visitor,
            "process_parameters_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitTosStatement(tos_statement_context, current_tos)

        mock.assert_called_once()

        # test Event statement
        event_statement_context = PFDLParser.EventStatementContext(None)
        tos_statement_context.children = [event_statement_context]

        with patch.object(
            self.mf_plugin_visitor,
            "process_event_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitTosStatement(tos_statement_context, current_tos)

        mock.assert_called_once()

        # test OnDone
        on_done_statement_context = PFDLParser.OnDoneStatementContext(None)
        tos_statement_context.children = [on_done_statement_context]

        with patch.object(
            self.mf_plugin_visitor,
            "process_on_done_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitTosStatement(tos_statement_context, current_tos)
        mock.assert_called_once()

    def test_visitLocationStatement(self):
        mock_component = TransportOrderStep()
        self.mf_plugin_visitor.current_program_component = mock_component

        location_context = PFDLParser.LocationStatementContext(None)
        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "location_id", location_context)
        location_name = self.mf_plugin_visitor.visitLocationStatement(location_context)
        self.assertEqual(location_name, "location_id")
        self.assertEqual(mock_component.context_dict["Location"], location_context)

    def test_visitParameterStatement(self):
        mock_component = TransportOrderStep()
        self.mf_plugin_visitor.current_program_component = mock_component

        parameter_stmt_context = PFDLParser.ParameterStatementContext(None)
        parameter_stmt_context.children = [PFDLParser.ValueContext(None)]

        with patch.object(
            self.mf_plugin_visitor,
            "visitValue",
            MagicMock(side_effect=["value"]),
        ):
            parameter = self.mf_plugin_visitor.visitParameterStatement(parameter_stmt_context)
        self.assertEqual(parameter, "value")
        self.assertEqual(mock_component.context_dict["Parameter"], parameter_stmt_context)

        parameter_stmt_context.children = [PFDLParser.Json_objectContext(None)]
        with patch.object(
            self.mf_plugin_visitor,
            "visitJson_object",
            MagicMock(side_effect=[{"id": "test"}]),
        ):
            parameter = self.mf_plugin_visitor.visitParameterStatement(parameter_stmt_context)
        self.assertTrue(isinstance(parameter, Dict))

    def test_visitOnDoneStatement(self):
        on_done_stmt_context = PFDLParser.OnDoneStatementContext(None)
        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "task_id", on_done_stmt_context)
        task_name = self.mf_plugin_visitor.visitOnDoneStatement(on_done_stmt_context)
        self.assertEqual(task_name, "task_id")

    def test_visitMoveOrderStep(self):
        move_order_step_context = PFDLParser.MoveOrderStepContext(None)
        move_order_step_context.children = [
            PFDLParser.MosStatementContext(None),
            PFDLParser.MosStatementContext(None),
        ]
        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "mos_id", move_order_step_context)

        # check if mos statement method is called
        with patch.object(self.mf_plugin_visitor, "visitMosStatement", return_value=None) as mock:
            move_order_step = self.mf_plugin_visitor.visitMoveOrderStep(move_order_step_context)

        self.assertEqual(mock.call_count, 2)
        self.assertIsNotNone(move_order_step)
        self.assertEqual(move_order_step.name, "mos_id")
        self.assertEqual(move_order_step.context, move_order_step_context)
        self.assertEqual(self.mf_plugin_visitor.current_program_component, move_order_step)

    def test_visitMosStatement(self):
        # test Location statement
        mos_statement_context = PFDLParser.MosStatementContext(None)
        mos_statement_context.children = [PFDLParser.LocationStatementContext(None)]

        current_mos = MoveOrderStep()
        with patch.object(
            self.mf_plugin_visitor,
            "process_location_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitMosStatement(mos_statement_context, current_mos)
        mock.assert_called_once()

        # test Event statement
        event_statement_context = PFDLParser.EventStatementContext(None)
        mos_statement_context.children = [event_statement_context]

        with patch.object(
            self.mf_plugin_visitor,
            "process_event_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitMosStatement(mos_statement_context, current_mos)
        mock.assert_called_once()

        # test OnDone
        on_done_statement_context = PFDLParser.OnDoneStatementContext(None)
        mos_statement_context.children = [on_done_statement_context]

        with patch.object(
            self.mf_plugin_visitor,
            "process_on_done_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitMosStatement(mos_statement_context, current_mos)
        mock.assert_called_once()

    def test_visitActionOrderStep(self):
        action_order_step_context = PFDLParser.ActionOrderStepContext(None)
        action_order_step_context.children = [
            PFDLParser.AosStatementContext(None),
            PFDLParser.AosStatementContext(None),
        ]

        create_and_add_token(
            PFDLParser.STARTS_WITH_LOWER_C_STR, "aos_id", action_order_step_context
        )

        # check if aosStatement method is called
        with patch.object(self.mf_plugin_visitor, "visitAosStatement", return_value=None) as mock:
            action_order_step = self.mf_plugin_visitor.visitActionOrderStep(
                action_order_step_context
            )

        self.assertEqual(mock.call_count, 2)
        self.assertIsNotNone(action_order_step)
        self.assertEqual(action_order_step.name, "aos_id")
        self.assertEqual(action_order_step.context, action_order_step_context)
        self.assertEqual(self.mf_plugin_visitor.current_program_component, action_order_step)

    def test_visitAosStatement(self):
        aos_statement_context = PFDLParser.AosStatementContext(None)
        current_aos = ActionOrderStep()

        # test Parameter statement
        aos_statement_context.children = [PFDLParser.ParameterStatementContext(None)]
        with patch.object(
            self.mf_plugin_visitor,
            "process_parameters_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitAosStatement(aos_statement_context, current_aos)

        mock.assert_called_once()

        # test Event statement
        event_statement_context = PFDLParser.EventStatementContext(None)
        aos_statement_context.children = [event_statement_context]

        with patch.object(
            self.mf_plugin_visitor,
            "process_event_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitAosStatement(aos_statement_context, current_aos)

        mock.assert_called_once()

        # test OnDone
        on_done_statement_context = PFDLParser.OnDoneStatementContext(None)
        aos_statement_context.children = [on_done_statement_context]

        with patch.object(
            self.mf_plugin_visitor,
            "process_on_done_statement",
            MagicMock(side_effect=None),
        ) as mock:
            self.mf_plugin_visitor.visitAosStatement(aos_statement_context, current_aos)
        mock.assert_called_once()

    def test_visitPrimitive(self):
        primitive_context = PFDLParser.PrimitiveContext(None)
        create_and_add_token(PFDLParser.NUMBER_P, "number", primitive_context)
        struct_id = self.mf_plugin_visitor.visitPrimitive(primitive_context)
        self.assertEqual(struct_id, "number")

        primitive_context = PFDLParser.PrimitiveContext(None)
        create_and_add_token(PFDLParser.STRING_P, "string", primitive_context)
        struct_id = self.mf_plugin_visitor.visitPrimitive(primitive_context)
        self.assertEqual(struct_id, "string")

        primitive_context = PFDLParser.PrimitiveContext(None)
        create_and_add_token(PFDLParser.BOOLEAN_P, "boolean", primitive_context)
        struct_id = self.mf_plugin_visitor.visitPrimitive(primitive_context)
        self.assertEqual(struct_id, "boolean")

        primitive_context = PFDLParser.PrimitiveContext(None)
        create_and_add_token(PFDLParser.LOCATION, "Location", primitive_context)
        struct_id = self.mf_plugin_visitor.visitPrimitive(primitive_context)
        self.assertEqual(struct_id, "Location")

        primitive_context = PFDLParser.PrimitiveContext(None)
        create_and_add_token(PFDLParser.TIME, "Time", primitive_context)
        struct_id = self.mf_plugin_visitor.visitPrimitive(primitive_context)
        self.assertEqual(struct_id, "Time")

        primitive_context = PFDLParser.PrimitiveContext(None)
        create_and_add_token(PFDLParser.STARTS_WITH_LOWER_C_STR, "an_id", primitive_context)
        struct_id = self.mf_plugin_visitor.visitPrimitive(primitive_context)
        self.assertEqual(struct_id, "an_id")

    def test_reprocess_order_steps(self):
        process = Process()
        process.tasks = {"task_1": Task(name="task_1"), "task_2": Task(name="task_2")}
        process.transport_order_steps = {"tos": TransportOrderStep(name="tos")}
        process.move_order_steps = {
            "mos": MoveOrderStep(name="mos"),
        }

        with patch.object(self.mf_plugin_visitor, "find_order_steps", MagicMock(side_effect=None)):
            with patch.object(
                self.mf_plugin_visitor, "add_locations_to_order_step", MagicMock(side_effect=None)
            ) as mock:
                self.mf_plugin_visitor.reprocess_order_steps(process)

        # once per order step
        self.assertEqual(mock.call_count, 2)

    def test_find_order_steps(self):
        process = Process()
        task = Task(name="task_1")
        process.tasks = {"task_1": task}

        # test TransportOrder
        to = TransportOrder(
            pickup_tos_names=["pickup_tos_1", "pickup_tos_2"],
            delivery_tos_names=["delivery_tos_1", "delivery_tos_2"],
        )

        pickup_tos_1 = TransportOrderStep(name="pickup_tos_1")
        pickup_tos_2 = TransportOrderStep(name="pickup_tos_2")
        delivery_tos_1 = TransportOrderStep(name="delivery_tos_1")
        delivery_tos_2 = TransportOrderStep(name="delivery_tos_2")

        statements = [to]
        with patch.object(
            self.mf_plugin_visitor,
            "get_order_step",
            MagicMock(side_effect=[pickup_tos_1, pickup_tos_2, delivery_tos_1, delivery_tos_2]),
        ):
            self.mf_plugin_visitor.find_order_steps(statements, task, process)

        self.assertEqual(to.pickup_tos, [pickup_tos_1, pickup_tos_2])
        self.assertEqual(to.delivery_tos, [delivery_tos_1, delivery_tos_2])

        # test MoveOrder
        mo = MoveOrder(move_order_step_name="mos")
        mos = MoveOrderStep(name="mos")

        statements = [mo]
        with patch.object(
            self.mf_plugin_visitor,
            "get_order_step",
            MagicMock(side_effect=[mos]),
        ):
            self.mf_plugin_visitor.find_order_steps(statements, task, process)

        self.assertEqual(mo.move_order_step, mos)

        # test ActionOrder
        ao = ActionOrder(action_order_step_name="aos")
        aos = ActionOrderStep(name="aos")
        statements = [ao]

        with patch.object(
            self.mf_plugin_visitor,
            "get_order_step",
            MagicMock(side_effect=[aos]),
        ):
            self.mf_plugin_visitor.find_order_steps(statements, task, process)

        self.assertEqual(ao.action_order_step, aos)

        # test multiple statements
        mo.move_order_step = None
        ao.action_order_step = None
        statements = [mo, ao]

        with patch.object(
            self.mf_plugin_visitor,
            "get_order_step",
            MagicMock(side_effect=[mos, aos]),
        ):
            self.mf_plugin_visitor.find_order_steps(statements, task, process)

        self.assertEqual(mo.move_order_step, mos)
        self.assertEqual(ao.action_order_step, aos)

        # test Condition
        mo.move_order_step = None
        condition = Condition(passed_stmts=[mo])
        statements = [condition]

        class DummyClass:
            pass

        with patch.object(
            self.mf_plugin_visitor,
            "get_order_step",
            MagicMock(side_effect=[mos]),
        ):
            with patch.object(
                self.mf_plugin_visitor.pfdl_base_classes,
                "get_class",
                MagicMock(side_effect=[Condition, DummyClass, DummyClass, DummyClass]),
            ):
                self.mf_plugin_visitor.find_order_steps(statements, task, process)

        self.assertEqual(mo.move_order_step, mos)

        mo.move_order_step = None
        condition = Condition(failed_stmts=[mo])
        statements = [condition]

        with patch.object(
            self.mf_plugin_visitor,
            "get_order_step",
            MagicMock(side_effect=[mos]),
        ):
            with patch.object(
                self.mf_plugin_visitor.pfdl_base_classes,
                "get_class",
                MagicMock(side_effect=[Condition, DummyClass, DummyClass, DummyClass]),
            ):
                self.mf_plugin_visitor.find_order_steps(statements, task, process)

        self.assertEqual(mo.move_order_step, mos)

        # test WhileLoop
        mo.move_order_step = None
        while_loop = WhileLoop(statements=[mo])
        statements = [while_loop]

        with patch.object(
            self.mf_plugin_visitor,
            "get_order_step",
            MagicMock(side_effect=[mos]),
        ):
            with patch.object(
                self.mf_plugin_visitor.pfdl_base_classes,
                "get_class",
                MagicMock(
                    side_effect=[
                        DummyClass,
                        WhileLoop,
                        DummyClass,
                        DummyClass,
                        DummyClass,
                        DummyClass,
                    ]
                ),
            ):
                self.mf_plugin_visitor.find_order_steps(statements, task, process)

        self.assertEqual(mo.move_order_step, mos)

        # test CountingLoop
        mo.move_order_step = None
        counting_loop = CountingLoop(statements=[mo])
        statements = [counting_loop]

        with patch.object(
            self.mf_plugin_visitor,
            "get_order_step",
            MagicMock(side_effect=[mos]),
        ):
            with patch.object(
                self.mf_plugin_visitor.pfdl_base_classes,
                "get_class",
                MagicMock(
                    side_effect=[
                        DummyClass,
                        CountingLoop,
                        DummyClass,
                        DummyClass,
                        DummyClass,
                        DummyClass,
                    ]
                ),
            ):
                self.mf_plugin_visitor.find_order_steps(statements, task, process)

        self.assertEqual(mo.move_order_step, mos)

    def test_get_order_step(self):
        process = Process()
        task = Task(name="task")

        # test TransportOrder
        to = TransportOrder(
            pickup_tos_names=["tos"],
            delivery_tos_names=["delivery_tos_1", "delivery_tos_2"],
        )
        tos = TransportOrderStep(name="tos")
        # order step is contained in order step dict
        tos_dict = {"tos": tos}

        order_step = self.mf_plugin_visitor.get_order_step("tos", tos_dict, task, process, to)
        self.assertEqual(order_step, tos)

        # order step is contained in task variables
        tos_dict = {}
        task.variables = {"tos": tos}
        with patch.object(
            self.mf_plugin_visitor, "add_locations_to_order_step", MagicMock(side_effect=None)
        ):
            order_step = self.mf_plugin_visitor.get_order_step("tos", tos_dict, task, process, to)
        self.assertEqual(order_step.location_name, "tos")

        # test MoveOrder
        mo = MoveOrder(move_order_step_name="mos")
        mos = MoveOrderStep(name="mos")
        # order step is contained in order step dict
        mos_dict = {"mos": mos}

        order_step = self.mf_plugin_visitor.get_order_step("mos", mos_dict, task, process, mo)
        self.assertEqual(order_step, mos)

        # order step is contained in task variables
        mos_dict = {}
        task.variables = {"mos": mos}
        with patch.object(
            self.mf_plugin_visitor, "add_locations_to_order_step", MagicMock(side_effect=None)
        ):
            order_step = self.mf_plugin_visitor.get_order_step("mos", mos_dict, task, process, mo)
        self.assertEqual(order_step.location_name, "mos")

        # test ActionOrder
        ao = ActionOrder(action_order_step_name="aos")
        aos = ActionOrderStep(name="aos")
        # order step is contained in order step dict
        aos_dict = {"aos": aos}

        order_step = self.mf_plugin_visitor.get_order_step("aos", aos_dict, task, process, ao)
        self.assertEqual(order_step, aos)

        # test unknown order (should cause an error)
        self.assert_print_error_is_called(
            self.mf_plugin_visitor.get_order_step, "aos_2", aos_dict, task, process, ao
        )

    def test_add_locations_to_order_step(self):
        process = Process()
        location_instance = Instance(
            name="location", struct_name="Location", attributes={"type": "test_type"}
        )
        process.instances = {"location": location_instance}
        to = TransportOrderStep(location_name="location")
        self.mf_plugin_visitor.add_locations_to_order_step(to, process)
        self.assertEqual(to.location, location_instance)

        # location name included in task variable
        task_variables = {"location": "Location"}
        process.instances = {}
        to = TransportOrderStep(location_name="location")
        self.mf_plugin_visitor.add_locations_to_order_step(to, process, task_variables)
        self.assertEqual(to.location.name, location_instance.name)
        self.assertEqual(to.location.struct_name, location_instance.struct_name)

        # struct is inherited from Location
        to = TransportOrderStep(location_name="inherited_location")
        to.context_dict["Location"] = {"location": PFDLParser.OrderStepContext}
        inherited_location_instance = Instance(
            name="inherited_location",
            struct_name="InheritedLocation",
            attributes={"type": "test_type"},
        )
        process.instances = {"inherited_location": inherited_location_instance}
        process.structs = {
            "InheritedLocation": Struct(name="InheritedLocation"),
            "Location": Struct(name="Location"),
        }
        with patch(
            "pfdl_scheduler.utils.helpers.get_parent_struct_names",
            MagicMock(side_effect=[(["Location"], None)]),
        ):
            self.mf_plugin_visitor.add_locations_to_order_step(to, process, task_variables)

        self.assertEqual(to.location.name, inherited_location_instance.name)
        self.assertEqual(to.location.struct_name, inherited_location_instance.struct_name)
        self.assertEqual(self.mf_plugin_visitor.error_handler.total_error_count, 0)

        # struct is no Location
        with patch(
            "pfdl_scheduler.utils.helpers.get_parent_struct_names",
            MagicMock(side_effect=[([], None)]),
        ):
            self.assert_print_error_is_called(
                self.mf_plugin_visitor.add_locations_to_order_step, to, process, task_variables
            )

        # order step unknown
        process = Process()
        self.assert_print_error_is_called(
            self.mf_plugin_visitor.add_locations_to_order_step, to, process, {}
        )

    def test_process_event_statement(self):
        # run test for all possible input types
        program_components = [Task(), TransportOrderStep(), MoveOrderStep(), ActionOrderStep()]
        component_statements_context = [
            PFDLParser.TaskStatementContext(None),
            PFDLParser.TosStatementContext(None),
            PFDLParser.MosStatementContext(None),
            PFDLParser.AosStatementContext(None),
        ]

        for program_component, component_statement_context in zip(
            program_components, component_statements_context
        ):
            # test StartedBy
            event_statement_context = PFDLParser.EventStatementContext(None)
            component_statement_context.children = [event_statement_context]
            create_and_add_token(PFDLParser.STARTED_BY, "StartedBy", event_statement_context)

            expression = {"left": "event.an_int", "binOp": "!=", "right": 20}

            with patch.object(
                self.mf_plugin_visitor,
                "visitEventStatement",
                MagicMock(side_effect=[expression]),
            ):
                self.mf_plugin_visitor.process_event_statement(
                    component_statement_context, program_component
                )

            self.assertEqual(program_component.context_dict["StartedBy"], event_statement_context)
            self.assertEqual(program_component.started_by_expr, expression)

            # try to add another StartedBy (should raise an error)

            expression_2 = {"left": "event.an_int", "binOp": "!=", "right": 10}

            with patch.object(
                self.mf_plugin_visitor,
                "visitEventStatement",
                MagicMock(side_effect=[expression_2]),
            ):
                self.assert_print_error_is_called(
                    self.mf_plugin_visitor.process_event_statement,
                    component_statement_context,
                    program_component,
                )

            # test FinishedBy
            event_statement_context = PFDLParser.EventStatementContext(None)
            component_statement_context.children = [event_statement_context]
            create_and_add_token(PFDLParser.FINISHED_BY, "FinishedBy", event_statement_context)

            expression = {"left": "event.an_int", "binOp": "!=", "right": 20}

            with patch.object(
                self.mf_plugin_visitor,
                "visitEventStatement",
                MagicMock(side_effect=[expression]),
            ):
                self.mf_plugin_visitor.process_event_statement(
                    component_statement_context, program_component
                )

            self.assertEqual(program_component.context_dict["FinishedBy"], event_statement_context)
            self.assertEqual(program_component.finished_by_expr, expression)

            # try to add another StartedBy (should raise an error)

            expression_2 = {"left": "event.an_int", "binOp": "!=", "right": 10}

            with patch.object(
                self.mf_plugin_visitor,
                "visitEventStatement",
                MagicMock(side_effect=[expression_2]),
            ):
                self.assert_print_error_is_called(
                    self.mf_plugin_visitor.process_event_statement,
                    component_statement_context,
                    program_component,
                )

    def test_process_location_statement(self):
        # run test for all possible input types
        order_steps = [TransportOrderStep(), MoveOrderStep()]
        component_statements_context = [
            PFDLParser.TosStatementContext(None),
            PFDLParser.MosStatementContext(None),
        ]

        for program_component, component_statement_context in zip(
            order_steps, component_statements_context
        ):
            self.mf_plugin_visitor.current_program_component = program_component
            location_statement_context = PFDLParser.LocationStatementContext(None)
            component_statement_context.children = [location_statement_context]
            create_and_add_token(
                PFDLParser.STARTS_WITH_LOWER_C_STR, "location", location_statement_context
            )

            location_name = "location_id"
            with patch.object(
                self.mf_plugin_visitor,
                "visitLocationStatement",
                MagicMock(side_effect=[location_name]),
            ):
                self.mf_plugin_visitor.process_location_statement(
                    component_statement_context, program_component
                )
            self.assertEqual(program_component.location_name, location_name)

            # try to add another Location (should raise an error)

            location_name_2 = "location_2_id"
            with patch.object(
                self.mf_plugin_visitor,
                "visitLocationStatement",
                MagicMock(side_effect=[location_name_2]),
            ):
                self.assert_print_error_is_called(
                    self.mf_plugin_visitor.process_location_statement,
                    component_statement_context,
                    program_component,
                )

    def test_parameters_statement(self):
        # run test for all possible input types
        order_steps = [TransportOrderStep(), ActionOrderStep()]
        component_statements_context = [
            PFDLParser.TosStatementContext(None),
            PFDLParser.AosStatementContext(None),
        ]

        for program_component, component_statement_context in zip(
            order_steps, component_statements_context
        ):
            self.mf_plugin_visitor.current_program_component = program_component
            parameters_statement_context = PFDLParser.ParameterStatementContext(None)
            component_statement_context.children = [parameters_statement_context]
            create_and_add_token(
                PFDLParser.STARTS_WITH_LOWER_C_STR, "parameter", parameters_statement_context
            )

            parameters = {"success": "true"}
            with patch.object(
                self.mf_plugin_visitor,
                "visitParameterStatement",
                MagicMock(side_effect=[parameters]),
            ):
                self.mf_plugin_visitor.process_parameters_statement(
                    component_statement_context, program_component
                )
            self.assertEqual(program_component.parameters, parameters)

            # try to add more Parameters (should raise an error)

            parameters_2 = {"success": "true"}
            with patch.object(
                self.mf_plugin_visitor,
                "visitParameterStatement",
                MagicMock(side_effect=[parameters_2]),
            ):
                self.assert_print_error_is_called(
                    self.mf_plugin_visitor.process_parameters_statement,
                    component_statement_context,
                    program_component,
                )

    def test_process_on_done_statement(self):
        # run test for all possible input types
        order_steps = [TransportOrderStep(), MoveOrderStep(), ActionOrderStep()]
        component_statements_context = [
            PFDLParser.TosStatementContext(None),
            PFDLParser.MosStatementContext(None),
            PFDLParser.AosStatementContext(None),
        ]

        for program_component, component_statement_context in zip(
            order_steps, component_statements_context
        ):
            self.mf_plugin_visitor.current_program_component = program_component
            on_done_statement_context = PFDLParser.OnDoneStatementContext(None)
            component_statement_context.children = [on_done_statement_context]
            create_and_add_token(
                PFDLParser.STARTS_WITH_LOWER_C_STR, "on_done", on_done_statement_context
            )

            follow_up_task_name = "follow_up_task"
            with patch.object(
                self.mf_plugin_visitor,
                "visitOnDoneStatement",
                MagicMock(side_effect=[follow_up_task_name]),
            ):
                self.mf_plugin_visitor.process_on_done_statement(
                    component_statement_context, program_component
                )
            self.assertEqual(program_component.follow_up_task_name, follow_up_task_name)

            # try to add another OnDone Task (should raise an error)

            follow_up_task_name_2 = "follow_up_task_2"
            with patch.object(
                self.mf_plugin_visitor,
                "visitOnDoneStatement",
                MagicMock(side_effect=[follow_up_task_name_2]),
            ):
                self.assert_print_error_is_called(
                    self.mf_plugin_visitor.process_on_done_statement,
                    component_statement_context,
                    program_component,
                )


def create_and_add_token(
    token_type: int, token_text: str, antlr_context: ParserRuleContext
) -> None:
    """Helper function to create a ANTLR Token object and to add
    it to the context object in one row."""
    token = Token()
    token.type = token_type
    token.text = token_text
    antlr_context.addTokenNode(token)
