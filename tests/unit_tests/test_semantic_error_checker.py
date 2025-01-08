# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains unit tests tests for the Scheduler class.

In the SemanticErrorChecker class, the model of the PFDL file is checked for static semantic errors.
If all methods in the visitor are correct, the model should not contain unexpected values. Thats
why there will be no checks for unexpected input args. Many methods are used to call a set of 
other tests methods. Here, mock objects are used to check if certain methods were called.

Transfered from the parent PFDL repository.
"""

# standard libraries
import unittest
from unittest.mock import MagicMock, patch

# third party libraries
from antlr4.ParserRuleContext import ParserRuleContext

# local sources
from pfdl_scheduler.model.instance import Instance
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.process import Process
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.rule import Rule
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.struct import Struct
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.task import Task
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order import TransportOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order_step import TransportOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order import MoveOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order_step import MoveOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order import ActionOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order_step import ActionOrderStep


from pfdl_scheduler.validation.error_handler import ErrorHandler
from pfdl_scheduler.model.condition import Condition
from pfdl_scheduler.model.service import Service
from pfdl_scheduler.model.task_call import TaskCall
from pfdl_scheduler.model.counting_loop import CountingLoop
from pfdl_scheduler.model.while_loop import WhileLoop
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.validation.semantic_error_checker import (
    SemanticErrorChecker,
)
from pfdl_scheduler.validation.semantic_error_checker import (
    SemanticErrorChecker as BaseSemanticErrorChecker,
)
import pfdl_scheduler.plugins.mf_plugin.mf_plugin.helpers as MFPluginHelpers


# global defines
from pfdl_scheduler.parser.pfdl_tree_visitor import IN_KEY, OUT_KEY


class DummyStart:
    def __init__(self):
        self.line = 0
        self.column = 0
        self.text = ""


class DummyContext:
    def __init__(self):
        self.start = DummyStart()


class TestSemanticErrorChecker(unittest.TestCase):
    """Tests the methods of the SemanticErrorChecker.

    Most methods will require a created Process object
    """

    def setUp(self):
        self.process = Process()
        self.error_handler = ErrorHandler("", False)
        self.checker = SemanticErrorChecker(self.error_handler, self.process)
        self.dummy_context = DummyContext()

    def check_method(self, method_name: str, return_value: bool, calls: int, method, *args) -> bool:
        """Runs the given method with the help of a mock object which emulates a function.

        Args:
            method_name: The mock function which should be emulated.
            return_value: The return value of the mock function.
            calls: Specifies how many times the mock method should be called to pass the test.
            method: The method which should be tested.
            args: Variable amount of arguments for the method to be tested.
        """
        result = None
        with patch.object(self.checker, method_name, return_value=return_value) as mock:
            result = method(*args)
        self.assertEqual(mock.call_count, calls)
        return result

    def assert_print_error_is_called(self, method, *args) -> None:
        """Runs the given method with the help of a mock object and checks if print error is called.

        Args:
            method: The method which should be tested.
            args: Variable amount of arguments for the method to be tested.
        """
        with patch.object(self.error_handler, "print_error") as mock:
            method(*args)
        mock.assert_called()

    def test_validate_process(self):
        transport_order_steps = {"tos": TransportOrderStep(name="tos")}
        move_order_steps = {
            "mos": MoveOrderStep(name="mos"),
        }
        action_order_steps = {"aos": ActionOrderStep(name="aos")}

        self.process.transport_order_steps = transport_order_steps
        self.process.move_order_steps = move_order_steps
        self.process.action_order_steps = action_order_steps

        with patch.object(
            BaseSemanticErrorChecker,
            "validate_process",
            MagicMock(side_effect=[True, False, True, True, True]),
        ) as base_validate_process_mock:
            with patch.object(
                SemanticErrorChecker,
                "check_order_steps",
                MagicMock(
                    side_effect=[
                        True,
                        True,
                        True,
                        True,
                        True,
                        True,
                        False,
                        True,
                        True,
                        True,
                        False,
                        True,
                        True,
                        True,
                        False,
                    ]
                ),
            ) as check_order_steps_mock:
                valid = self.checker.validate_process()
                invalid_process = self.checker.validate_process()
                invalid_tos = self.checker.validate_process()
                invalid_mos = self.checker.validate_process()
                invalid_aos = self.checker.validate_process()

        # check if an error in each of the methods affects the return value
        self.assertTrue(valid)
        self.assertFalse(invalid_process)
        self.assertFalse(invalid_tos)
        self.assertFalse(invalid_mos)
        self.assertFalse(invalid_aos)

        # check if all methods are called at each run
        self.assertEqual(base_validate_process_mock.call_count, 5)
        self.assertEqual(check_order_steps_mock.call_count, 15)  # called 3 times per run

    def test_check_statement(self):
        task = Task()
        base_statements = [Service(), TaskCall(), WhileLoop, CountingLoop, Condition()]
        mf_plugin_statements = [TransportOrder(), MoveOrder(), ActionOrder()]

        for statement in base_statements:
            with patch.object(
                BaseSemanticErrorChecker, "check_statement", MagicMock(return_value=True)
            ) as base_check_statement_mock:
                is_statement_valid = self.checker.check_statement(statement, task)

            base_check_statement_mock.assert_called_once_with(self.checker, statement, task)
            self.assertTrue(is_statement_valid)

            # test if error in base method effects the return value
            with patch.object(
                BaseSemanticErrorChecker, "check_statement", MagicMock(return_value=False)
            ) as base_check_statement_mock:
                is_statement_valid = self.checker.check_statement(statement, task)

            self.assertFalse(is_statement_valid)

        # test if MF-Plugin statements are skipped
        for statement in mf_plugin_statements:
            with patch.object(
                BaseSemanticErrorChecker, "check_statement", MagicMock(return_value=False)
            ) as base_check_statement_mock:
                is_statement_valid = self.checker.check_statement(statement, task)

            base_check_statement_mock.assert_not_called()
            self.assertTrue(is_statement_valid)

    def test_check_instances(self):
        empty_instances_valid = self.checker.check_instances()
        self.assertTrue(empty_instances_valid)

        test_instance = Instance("testInstance", struct_name="TestStruct")
        test_struct = Struct("TestStruct")
        self.process.instances = {"testInstance": test_instance}
        self.process.structs = {"TestStruct": test_struct}

        # test valid case
        with patch.object(
            SemanticErrorChecker,
            "check_if_instance_attributes_exist_in_struct",
            MagicMock(side_effect=[True]),
        ):
            with patch.object(
                SemanticErrorChecker,
                "check_if_value_matches_with_defined_type",
                MagicMock(side_effect=[True]),
            ):
                with patch.object(
                    SemanticErrorChecker,
                    "check_if_struct_attributes_are_assigned",
                    MagicMock(side_effect=[True]),
                ):
                    is_instance_valid = self.checker.check_instances()

        self.assertTrue(is_instance_valid)

        # test invalid cases
        with patch.object(
            SemanticErrorChecker,
            "check_if_instance_attributes_exist_in_struct",
            MagicMock(side_effect=[False]),
        ):
            with patch.object(
                SemanticErrorChecker,
                "check_if_value_matches_with_defined_type",
                MagicMock(side_effect=[True]),
            ) as value_matches_mock:
                with patch.object(
                    SemanticErrorChecker,
                    "check_if_struct_attributes_are_assigned",
                    MagicMock(side_effect=[True]),
                ) as struct_attributes_assigned_mock:
                    is_instance_valid = self.checker.check_instances()

        self.assertFalse(is_instance_valid)
        value_matches_mock.assert_not_called()
        struct_attributes_assigned_mock.assert_called()

        with patch.object(
            SemanticErrorChecker,
            "check_if_instance_attributes_exist_in_struct",
            MagicMock(side_effect=[True]),
        ):
            with patch.object(
                SemanticErrorChecker,
                "check_if_value_matches_with_defined_type",
                MagicMock(side_effect=[False]),
            ) as value_matches_mock:
                with patch.object(
                    SemanticErrorChecker,
                    "check_if_struct_attributes_are_assigned",
                    MagicMock(side_effect=[True]),
                ) as struct_attributes_assigned_mock:
                    is_instance_valid = self.checker.check_instances()

        self.assertFalse(is_instance_valid)
        struct_attributes_assigned_mock.assert_called()

        with patch.object(
            SemanticErrorChecker,
            "check_if_instance_attributes_exist_in_struct",
            MagicMock(side_effect=[True]),
        ):
            with patch.object(
                SemanticErrorChecker,
                "check_if_value_matches_with_defined_type",
                MagicMock(side_effect=[True]),
            ) as value_matches_mock:
                with patch.object(
                    SemanticErrorChecker,
                    "check_if_struct_attributes_are_assigned",
                    MagicMock(side_effect=[False]),
                ) as struct_attributes_assigned_mock:
                    is_instance_valid = self.checker.check_instances()

        self.assertFalse(is_instance_valid)

        # test struct is not found, error should be printed
        self.process.structs = {}
        self.assert_print_error_is_called(self.checker.check_instances)

    def test_check_single_expression(self):
        task = Task()
        expression = "1"
        context = ParserRuleContext()

        # primitive single expressions should be evaluated by the base semantic error checker
        with patch.object(
            BaseSemanticErrorChecker,
            "check_single_expression",
            MagicMock(side_effect=[True, False]),
        ):
            valid_expression = self.checker.check_single_expression(expression, context, task)
            invalid_expression = self.checker.check_single_expression(expression, context, task)

        self.assertTrue(valid_expression)
        self.assertFalse(invalid_expression)

        expression = ["testInstance", "value"]
        with patch.object(
            SemanticErrorChecker, "check_attribute_access", MagicMock(side_effect=[False])
        ):
            no_attribute_access_valid = self.checker.check_single_expression(
                expression, context, task
            )

        self.assertFalse(no_attribute_access_valid)

        with patch.object(
            SemanticErrorChecker, "check_attribute_access", MagicMock(return_value=True)
        ):
            with patch(
                "pfdl_scheduler.utils.helpers.get_type_of_variable_list",
                MagicMock(side_effect=[["boolean", "string"], ["number", "string"], ["string"]]),
            ):
                with patch.object(
                    BaseSemanticErrorChecker,
                    "check_single_expression",
                    MagicMock(return_value=False),
                ) as base_check_single_expression_mock:
                    boolean_variable_type_valid = self.checker.check_single_expression(
                        expression, context, task
                    )
                    number_variable_type_valid = self.checker.check_single_expression(
                        expression, context, task
                    )
                    string_variable_type_valid = self.checker.check_single_expression(
                        expression, context, task
                    )

        self.assertTrue(boolean_variable_type_valid)
        self.assertTrue(number_variable_type_valid)
        # invalid type
        self.assertFalse(string_variable_type_valid)
        base_check_single_expression_mock.assert_called_once()

    def test_check_type_of_value(self):

        # test type list
        with patch.object(
            BaseSemanticErrorChecker,
            "check_type_of_value",
            MagicMock(side_effect=[True, False, False]),
        ) as base_method_mock:
            value_type = ["string", "boolean"]
            correct_value = "test_string"
            incorrect_value = 10

            string_valid = self.checker.check_type_of_value(correct_value, value_type)
            number_valid = self.checker.check_type_of_value(incorrect_value, value_type)

        self.assertTrue(string_valid)
        self.assertFalse(number_valid)
        self.assertEqual(base_method_mock.call_count, 3)

        # test single type
        with patch.object(
            BaseSemanticErrorChecker, "check_type_of_value", MagicMock(side_effect=[True, False])
        ) as base_method_mock:
            value_type = "string"
            correct_value = "test_string"
            incorrect_value = 10

            string_valid = self.checker.check_type_of_value(correct_value, value_type)
            number_valid = self.checker.check_type_of_value(incorrect_value, value_type)

        self.assertTrue(string_valid)
        self.assertFalse(number_valid)
        self.assertEqual(base_method_mock.call_count, 2)

    def test_check_tasks(self):
        correct_start_task = Task("productionTask", statements=TransportOrder())
        no_start_task = Task("noStartTask", statements=TransportOrder())
        no_statement_task = Task("productionTask")
        incorrect_started_by_task = Task(
            "productionTask", started_by_expr={"binOp": ">", "left": "faulty_string", "right": 0}
        )
        incorrect_finished_by_task = Task(
            "productionTask", finished_by_expr={"binOp": ">", "left": "faulty_string", "right": 0}
        )
        incorrect_constraints_task = Task(
            "productionTask", constraints={"binOp": ">", "left": "faulty_string", "right": 0}
        )

        with patch.object(
            BaseSemanticErrorChecker,
            "check_tasks",
            MagicMock(side_effect=[True, False, True, True, True, True, True]),
        ) as base_check_tasks_mock:
            with patch.object(
                SemanticErrorChecker,
                "check_task_statements",
                MagicMock(side_effect=[True, True, False, True, True, True, True, False]),
            ) as check_task_statements_mock:
                with patch.object(
                    SemanticErrorChecker,
                    "check_started_by",
                    MagicMock(side_effect=[True, True, True, False, True, True, True, True]),
                ) as check_started_by_mock:
                    with patch.object(
                        SemanticErrorChecker,
                        "check_finished_by",
                        MagicMock(side_effect=[True, True, True, True, False, True, True, True]),
                    ) as check_finished_by_mock:
                        with patch.object(
                            SemanticErrorChecker,
                            "check_constraints",
                            MagicMock(
                                side_effect=[True, True, True, True, True, False, True, True]
                            ),
                        ) as check_constraints_mock:
                            # valid program
                            self.checker.tasks = {"productionTask": correct_start_task}
                            self.process.tasks = {"productionTask": correct_start_task}

                            start_task_correct = self.checker.check_tasks()

                            # no start task, invalid
                            self.checker.tasks = {"noStartTask": no_start_task}
                            self.process.tasks = {"noStartTask": no_start_task}

                            start_task_missing_correct = self.checker.check_tasks()

                            # task with no statements, invalid
                            self.checker.tasks = {"productionTask": no_statement_task}
                            self.process.tasks = {"productionTask": no_statement_task}

                            no_statement_task_correct = self.checker.check_tasks()

                            # task with no statements, invalid
                            self.checker.tasks = {"productionTask": incorrect_started_by_task}
                            self.process.tasks = {"productionTask": incorrect_started_by_task}

                            incorrect_started_by_task_correct = self.checker.check_tasks()

                            # task with no statements, invalid
                            self.checker.tasks = {"productionTask": incorrect_finished_by_task}
                            self.process.tasks = {"productionTask": incorrect_finished_by_task}

                            incorrect_finished_by_task_correct = self.checker.check_tasks()

                            # task with no statements, invalid
                            self.checker.tasks = {"productionTask": incorrect_constraints_task}
                            self.process.tasks = {"productionTask": incorrect_constraints_task}

                            incorrect_constraints_task_correct = self.checker.check_tasks()

                            # multiple tasks, one is invalid
                            no_statement_task.name = "noStatementTask"

                            self.checker.tasks = {
                                "productionTask": correct_start_task,
                                "noStatementTask": no_statement_task,
                            }
                            self.process.tasks = {
                                "productionTask": correct_start_task,
                                "noStatementTask": no_statement_task,
                            }

                            incorrect_second_task_correct = self.checker.check_tasks()

        self.assertTrue(start_task_correct)
        self.assertFalse(start_task_missing_correct)
        self.assertFalse(no_statement_task_correct)
        self.assertFalse(incorrect_started_by_task_correct)
        self.assertFalse(incorrect_finished_by_task_correct)
        self.assertFalse(incorrect_constraints_task_correct)
        self.assertFalse(incorrect_second_task_correct)

        # should be called once per call
        self.assertEqual(base_check_tasks_mock.call_count, 7)

        # should be called once per task
        self.assertEqual(check_task_statements_mock.call_count, 8)
        self.assertEqual(check_started_by_mock.call_count, 8)
        self.assertEqual(check_finished_by_mock.call_count, 8)
        self.assertEqual(check_constraints_mock.call_count, 8)

    def test_check_task_statements(self):
        to_task = Task(statements=[TransportOrder()])

        to_task_correct = self.checker.check_task_statements(to_task)
        self.assertTrue(to_task_correct)

        # task without any orders
        condition_task = Task(statements=[Condition()])
        condition_task_correct = self.checker.check_task_statements(condition_task)
        self.assertTrue(condition_task_correct)

        # empty task
        empty_task = Task()
        empty_task_correct = self.checker.check_task_statements(empty_task)
        self.assertFalse(empty_task_correct)

        # task only with MoveOrder
        mo_task = Task(statements=[MoveOrder()])
        mo_task_correct = self.checker.check_task_statements(mo_task)
        self.assertFalse(mo_task_correct)

        # task only with ActionOrder
        ao_task = Task(statements=[ActionOrder()])
        ao_task_correct = self.checker.check_task_statements(ao_task)
        self.assertFalse(ao_task_correct)

        # task with multiple orders, TransportOrder first
        multiple_orders_valid = Task(statements=[TransportOrder(), MoveOrder(), ActionOrder()])
        multiple_orders_task_correct = self.checker.check_task_statements(multiple_orders_valid)
        self.assertTrue(multiple_orders_task_correct)

        # task with multiple orders, MoveOrder first
        multiple_orders_invalid = Task(statements=[MoveOrder(), TransportOrder()])
        multiple_orders_task_correct = self.checker.check_task_statements(multiple_orders_invalid)
        self.assertFalse(multiple_orders_task_correct)

        # task with multiple orders, ActionOrder first
        multiple_orders_invalid = Task(statements=[ActionOrder(), TransportOrder()])
        multiple_orders_task_correct = self.checker.check_task_statements(multiple_orders_invalid)
        self.assertFalse(multiple_orders_task_correct)

    def test_check_started_by(self):
        test_task = Task()
        test_task.context_dict = {"StartedBy": ParserRuleContext(None)}
        empty_expression_valid = self.checker.check_started_by(test_task)
        self.assertTrue(empty_expression_valid)

        with patch.object(
            SemanticErrorChecker, "check_expression", MagicMock(side_effect=[True, False])
        ):
            # correct expression
            test_task.started_by_expr = {"binOp": ">", "left": 10, "right": 0}
            valid_started_by_correct = self.checker.check_started_by(test_task)

            # incorrect expression
            test_task.started_by_expr = {"binOp": ">", "left": "faulty_string", "right": 0}
            invalid_started_by_correct = self.checker.check_started_by(test_task)

        self.assertTrue(valid_started_by_correct)
        self.assertFalse(invalid_started_by_correct)

    def test_check_finished_by(self):
        test_task = Task()
        test_task.context_dict = {"FinishedBy": ParserRuleContext(None)}
        empty_expression_valid = self.checker.check_finished_by(test_task)
        self.assertTrue(empty_expression_valid)

        with patch.object(
            SemanticErrorChecker, "check_expression", MagicMock(side_effect=[True, False])
        ):
            # correct expression
            test_task.finished_by_expr = {"binOp": ">", "left": 10, "right": 0}
            valid_finished_by_correct = self.checker.check_finished_by(test_task)

            # incorrect expression
            test_task.finished_by_expr = {"binOp": ">", "left": "faulty_string", "right": 0}
            invalid_finished_by_correct = self.checker.check_finished_by(test_task)

        self.assertTrue(valid_finished_by_correct)
        self.assertFalse(invalid_finished_by_correct)

    def test_check_constraints(self):
        test_task = Task()
        test_task.context_dict = {"Constraints": ParserRuleContext(None)}

        empty_expression_valid = self.checker.check_constraints(test_task)
        self.assertTrue(empty_expression_valid)

        test_task.constraints = {"testConstraintAttribute": 10}
        json_expression_valid = self.checker.check_constraints(test_task)
        self.assertTrue(json_expression_valid)

        with patch.object(
            SemanticErrorChecker, "check_expression", MagicMock(side_effect=[True, True, False])
        ) as base_check_expression_mock:
            # correct binOp expression
            test_task.constraints = {"binOp": ">", "left": 10, "right": 0}
            valid_binOp_constraints_correct = self.checker.check_constraints(test_task)

            # correct unOp expression
            test_task.constraints = {"value": 5}
            valid_unOp_constraints_correct = self.checker.check_constraints(test_task)

            # incorrect expression
            test_task.constraints = {"binOp": ">", "left": "faulty_string", "right": 0}
            invalid_constraints_correct = self.checker.check_constraints(test_task)

        self.assertTrue(valid_binOp_constraints_correct)
        self.assertTrue(valid_unOp_constraints_correct)
        self.assertFalse(invalid_constraints_correct)

        self.assertEqual(base_check_expression_mock.call_count, 3)

    def test_check_expression(self):
        task = Task()
        task.variables = {"variable": "test"}

        instance_1 = Instance(name="instance_1", struct_name="Struct1")
        instance_2 = Instance(name="instance_2", struct_name="Struct2")

        self.process.instances = {"instance_1": instance_1, "instance_2": instance_2}

        context = ParserRuleContext(None)

        # test task with variables
        with patch.object(
            BaseSemanticErrorChecker, "check_expression", MagicMock(side_effect=[True, False])
        ) as base_check_expression_mock:
            valid_expression = True
            invalid_expression = "invalid"

            valid_expression_correct = self.checker.check_expression(
                valid_expression, context, task
            )

            invalid_expression_correct = self.checker.check_expression(
                invalid_expression, context, task
            )

        self.assertTrue(valid_expression_correct)
        self.assertFalse(invalid_expression_correct)

        # test if dummy tasks copies variables
        dummy_task = base_check_expression_mock.call_args_list[0].args[3]
        self.assertEqual(dummy_task.variables, task.variables)

        task.variables = {}
        with patch.object(
            SemanticErrorChecker, "check_rule_call", MagicMock(side_effect=[True, False])
        ) as check_rule_call_mock:
            # correct expression
            valid_expression = ("existing_rule", {"argument_1": 5})
            valid_expression_correct = self.checker.check_expression(
                valid_expression, context, task
            )

            # incorrect expression
            invalid_expression = ("unknown_rule", {"argument_1": 5})
            invalid_expression_correct = self.checker.check_expression(
                invalid_expression, context, task
            )

        self.assertTrue(valid_expression_correct)
        self.assertFalse(invalid_expression_correct)

        # test if dummy tasks copies instances
        dummy_task = check_rule_call_mock.call_args_list[0].args[1]
        self.assertEqual(dummy_task.variables.keys(), self.process.instances.keys())

    def test_check_rule_call(self):
        test_rule = Rule(
            name="test_rule",
            parameters={"value1": None},
            expressions=[{"binOp": ">", "left": "value1", "right": 0}],
        )
        rule_call = ("test_rule", {"value1": 10})
        task = Task()
        context = ParserRuleContext(None)

        with patch.object(
            MFPluginHelpers,
            "substitute_parameter_in_expression",
            return_value={"binOp": ">", "left": 10, "right": 0},
        ):
            with patch.object(SemanticErrorChecker, "check_expression", return_value=True):

                # rule is not known to the process
                self.assert_print_error_is_called(
                    self.checker.check_rule_call, rule_call, task, context
                )

                # this should work
                self.process.rules = {"test_rule": test_rule}
                self.assertTrue(self.checker.check_rule_call(rule_call, task, context))

                # incomplete parameters
                test_rule.parameters = {"value1": None, "value_2": None}
                # rule_call_wrong_parameters = ("test_rule", {"value2": 10})
                self.assert_print_error_is_called(
                    self.checker.check_rule_call, rule_call, task, context
                )

                # incomplete parameters, but they have default values
                test_rule.parameters = {"value1": None, "value_2": True}
                self.assertTrue(self.checker.check_rule_call(rule_call, task, context))

        # expression is faulty
        with patch.object(
            MFPluginHelpers,
            "substitute_parameter_in_expression",
            return_value={"binOp": ">", "left": "error", "right": 0},
        ):
            with patch.object(SemanticErrorChecker, "check_expression", return_value=False):
                rule_call = ("test_rule", {"value1": "error"})

                self.assertFalse(self.checker.check_rule_call(rule_call, task, context))

    def test_order_steps(self):
        transport_order_step = TransportOrderStep(name="tos")
        move_order_step = MoveOrderStep(name="mos")
        action_order_step = ActionOrderStep(name="aos")

        order_steps = {
            "tos": transport_order_step,
            "mos": move_order_step,
            "aos": action_order_step,
        }

        with patch.object(SemanticErrorChecker, "check_on_done", return_value=True):
            with patch.object(SemanticErrorChecker, "check_on_done", return_value=True):
                with patch.object(SemanticErrorChecker, "check_on_done", return_value=True):
                    valid = self.checker.check_order_steps(order_steps)

        self.assertTrue(valid)

        # test combinations of errors

        with patch.object(
            SemanticErrorChecker,
            "check_on_done",
            MagicMock(side_effect=[False, True, True, True, True, True, True, True, True]),
        ) as check_on_done_mock:
            with patch.object(
                SemanticErrorChecker,
                "check_started_by",
                MagicMock(side_effect=[True, True, True, True, False, True, True, True, True]),
            ) as check_started_by_mock:
                with patch.object(
                    SemanticErrorChecker,
                    "check_finished_by",
                    MagicMock(side_effect=[True, True, True, True, True, True, True, True, False]),
                ) as check_finished_by_mock:
                    check_on_done_false = self.checker.check_order_steps(order_steps)
                    check_stared_by_false = self.checker.check_order_steps(order_steps)
                    check_finshed_by_false = self.checker.check_order_steps(order_steps)

        self.assertFalse(check_on_done_false)
        self.assertFalse(check_stared_by_false)
        self.assertFalse(check_finshed_by_false)

        # should all be called even if previous checks failed
        self.assertEqual(check_on_done_mock.call_count, 9)
        self.assertEqual(check_started_by_mock.call_count, 9)
        self.assertEqual(check_finished_by_mock.call_count, 9)

    def test_check_on_done(self):
        transport_order_step = TransportOrderStep(name="tos")

        # no follow up task, should be valid
        self.assertTrue(self.checker.check_on_done(transport_order_step))

        # unknown task
        transport_order_step.follow_up_task_name = "onDoneTask"
        self.assert_print_error_is_called(self.checker.check_on_done, transport_order_step)

        # known task
        on_done_task = Task(name="onDoneTask")
        self.checker.tasks = {"onDoneTask": on_done_task}
        self.assertTrue(self.checker.check_on_done(transport_order_step))
