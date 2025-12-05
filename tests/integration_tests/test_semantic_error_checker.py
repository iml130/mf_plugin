# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""Contains integration tests for the SemanticErrorChecker."""

# standard libraries
import unittest

# 3rd party libs
from antlr4.InputStream import InputStream
from antlr4.CommonTokenStream import CommonTokenStream

# local sources
## PFDL base sources
from pfdl_scheduler.plugins.plugin_loader import PluginLoader
from pfdl_scheduler.validation.error_handler import ErrorHandler

## MF-Plugin sources
from pfdl_scheduler.parser.PFDLLexer import PFDLLexer
from pfdl_scheduler.parser.PFDLParser import PFDLParser
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.parser.pfdl_tree_visitor import PFDLTreeVisitor
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.validation.semantic_error_checker import (
    SemanticErrorChecker,
)


TEST_FILE_FOLDER_PATH = "pfdl_scheduler/plugins/mf_plugin/tests/test_files/invalid/semantic/"

plugin_loader = PluginLoader()
plugin_loader.load_plugins(["mf_plugin/mf_plugin"])
pfdl_base_classes = plugin_loader.get_pfdl_base_classes()


class TestSemanticErrorChecker(unittest.TestCase):
    """Testcase containing integration tests for the SemanticErrorChecker.

    Attributes:
        lexer: The generated ANTLR Lexer for the MF-Plugin.
        parser: The generated ANTLR Parser for the MF-Plugin.
        self.mf_plugin_visitor: MFPluginVisitor instance.
        error_handler: ErrorHandler instance for couting the errors.
        semantic_error_checker: The SemanticErrorChecker instance which should be tested.
    """

    def setUp(self):
        self.lexer: PFDLLexer = None
        self.parser: PFDLParser = None
        self.mf_plugin_visitor: PFDLTreeVisitor = None
        self.error_handler: ErrorHandler = None
        self.semantic_error_checker: SemanticErrorChecker = None

    def load_file(self, test_file_name: str):
        """Loads a file from the given path and parses it if it is a MF-Plugin program."""

        file_path = TEST_FILE_FOLDER_PATH + test_file_name
        if file_path.endswith(".pfdl"):
            mf_plugin_string = ""
            with open(file_path, "r", encoding="utf8") as file:
                mf_plugin_string = file.read()

            self.lexer = PFDLLexer(InputStream(mf_plugin_string))
            token_stream = CommonTokenStream(self.lexer)
            self.parser = PFDLParser(token_stream)
            tree = self.parser.program()
            self.error_handler = ErrorHandler(file_path, file_path)

            self.mf_plugin_visitor = PFDLTreeVisitor(self.error_handler, pfdl_base_classes)
            mf_plugin_program = None
            if not self.error_handler.has_error():
                mf_plugin_program = self.mf_plugin_visitor.visitProgram(tree)
            self.semantic_error_checker = SemanticErrorChecker(
                self.error_handler, mf_plugin_program, pfdl_base_classes
            )

    def test_attribute_missing_in_nested_assignment(self):
        self.load_file("attribute_missing_in_nested_assignment.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_duplicate_components(self):
        self.load_file("duplicate_components.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 6)  # 6 duplicates

    def test_duplicate_parameter_name(self):
        self.load_file("duplicate_parameter_name.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_invalid_expression_in_constraints(self):
        self.load_file("invalid_expression_in_constraints.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_invalid_expression_in_finished_by(self):
        self.load_file("invalid_expression_in_finished_by.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_invalid_expression_in_started_by(self):
        self.load_file("invalid_expression_in_started_by.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_unknown_attribute_in_nested_assignment(self):
        self.load_file("unknown_attribute_in_nested_assignment.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_unknown_datatype_in_struct(self):
        self.load_file("unknown_datatype_in_struct.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_unknown_identifier_in_rule(self):
        self.load_file("unknown_identifier_in_rule.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_unknown_instance_in_location(self):
        self.load_file("unknown_instance_in_location.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_unknown_parent_struct(self):
        self.load_file("unknown_parent_struct.pfdl")
        # no semantic error checker here, because the error is already thown in the tree visitor
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_unknown_rule_name_in_rule_call(self):
        self.load_file("unknown_rule_name_in_rule_call.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_unknown_rule_name_in_rule_definition(self):
        self.load_file("unknown_rule_name_in_rule_definition.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_unknown_struct_in_instance(self):
        self.load_file("unknown_struct_in_instance.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_unknown_task_in_on_done(self):
        self.load_file("unknown_task_in_on_done.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)

    def test_value_dont_match_in_nested_attribute_assignment(self):
        self.load_file("value_dont_match_in_nested_attribute_assignment.pfdl")
        self.semantic_error_checker.validate_process()
        self.assertEqual(self.error_handler.semantic_error_count, 1)
