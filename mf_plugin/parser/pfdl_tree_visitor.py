# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""This class contains plugin code to overwrite the PFDL class PFDLTreeVisitor."""

# standard libraries
import json
from typing import Dict, List, Tuple, Union
import os.path as path
import uuid

# 3rd party
from antlr4.tree.Tree import TerminalNodeImpl

# local sources
## PFDL base sources
from pfdl_scheduler.model.instance import Instance
from pfdl_scheduler.pfdl_base_classes import PFDLBaseClasses
import pfdl_scheduler.plugins

from pfdl_scheduler.model.array import Array
from pfdl_scheduler.model.service import Service
from pfdl_scheduler.model.condition import Condition
from pfdl_scheduler.model.counting_loop import CountingLoop
from pfdl_scheduler.model.while_loop import WhileLoop
from pfdl_scheduler.model.parallel import Parallel
from pfdl_scheduler.model.task_call import TaskCall

from pfdl_scheduler.plugins.plugin_loader import base_class
from pfdl_scheduler.utils import helpers

from pfdl_scheduler.validation.error_handler import ErrorHandler

### only for unit tests
from pfdl_scheduler.plugins.parser.PFDLParserVisitor import PFDLParserVisitor


## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.process import Process
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.struct import Struct
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.task import Task
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.order_step import OrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order import TransportOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order_step import TransportOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order import MoveOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order_step import MoveOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order import ActionOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order_step import ActionOrderStep
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.rule import Rule

from pfdl_scheduler.plugins.parser.PFDLParser import PFDLParser

import pfdl_scheduler.plugins.mf_plugin.mf_plugin.helpers as mf_plugin_helpers


IN_KEY: str = "in"
OUT_KEY: str = "out"
START_TASK: str = "mainTask"


@base_class("PFDLTreeVisitor")
class PFDLTreeVisitor(pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor):
    def __init__(self, error_handler: ErrorHandler, pfdl_base_classes: PFDLBaseClasses) -> None:
        pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor.__init__(
            self, error_handler, pfdl_base_classes
        )

    def visitProgram(self, ctx):
        process = Process(start_task_name=START_TASK)
        for child in ctx.children:
            if child is not None and not isinstance(child, TerminalNodeImpl):  # a new line token
                program_component = self.visit(child)
                if program_component:
                    self.process_mf_plugin_component(program_component, process)

        # perform additional steps after visiting the syntax tree
        self.execute_additional_tasks(process)

        return process

    def process_mf_plugin_component(
        self,
        program_component: Union[
            Struct, Instance, Rule, Task, TransportOrderStep, MoveOrderStep, ActionOrderStep
        ],
        mf_plugin_program,
    ) -> None:
        """Checks the type of the program component and adds it to
        the corresponding dict inside the PFDL program."""
        components = {
            "Struct": mf_plugin_program.structs,
            "Instance": mf_plugin_program.instances,
            "Rule": mf_plugin_program.rules,
            "Task": mf_plugin_program.tasks,
            "TransportOrderStep": mf_plugin_program.transport_order_steps,
            "MoveOrderStep": mf_plugin_program.move_order_steps,
            "ActionOrderStep": mf_plugin_program.action_order_steps,
        }

        component_type = program_component.__class__.__name__
        if program_component.name not in components[component_type]:
            components[component_type][program_component.name] = program_component
        else:
            error_msg = f"A '{component_type}' with the name '{program_component.name}' was already defined."
            self.error_handler.print_error(error_msg, context=program_component.context)

    def visitStruct(self, ctx: PFDLParser.StructContext) -> Struct:
        struct = pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor.visitStruct(self, ctx)

        # set default attributes in every struct
        if "time" not in struct.attributes:
            struct.attributes["time"] = "number"
        if "id" not in struct.attributes:
            struct.attributes["id"] = "string"
        return struct

    def visitInstance(self, ctx: PFDLParser.InstanceContext) -> Instance:
        instance = pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor.visitInstance(self, ctx)

        if "time" not in instance.attributes:
            instance.attributes["time"] = 0
        if "id" not in instance.attributes:
            instance.attributes["id"] = str(uuid.uuid4())
        return instance

    def visitRule_(self, ctx: PFDLParser.Rule_Context) -> Rule:
        rule_name, rule_parameters = self.visitRule_call(ctx.rule_call())
        rule = Rule(name=rule_name, parameters=rule_parameters, context=ctx)
        self.current_program_component = rule
        for expression_context in ctx.expression():
            expression = self.visitExpression(expression_context)
            rule.expressions.append(expression)
        return rule

    def visitRule_call(
        self, ctx: PFDLParser.Rule_callContext
    ) -> Tuple[str, Dict[str, Union[None, str]]]:
        rule_name = ctx.STARTS_WITH_LOWER_C_STR().getText()
        rule_parameter = {}
        for rule_param_ctx in ctx.rule_parameter():
            parameter_name, parameter_value = self.visitRule_parameter(rule_param_ctx)
            if parameter_name in rule_parameter:
                error_msg = f"The parameter '{parameter_name}' was already defined."
                self.error_handler.print_error(error_msg, context=ctx)
            else:
                rule_parameter[parameter_name] = parameter_value
        return (rule_name, rule_parameter)

    def visitRule_parameter(
        self, ctx: PFDLParser.Rule_parameterContext
    ) -> Tuple[str, Union[None, str]]:
        parameter = ""
        if ctx.STARTS_WITH_LOWER_C_STR():
            parameter = ctx.STARTS_WITH_LOWER_C_STR().getText()
        else:
            parameter = self.visitValue(ctx.value()[0])
            # parameters in nested rule calls might not be casted, so do it here
            parameter = mf_plugin_helpers.cast_element(parameter)

        default_value = None
        if len(ctx.children) == 3:  # 3, because of the '='
            default_value = self.visitValue(ctx.children[2])

        return (parameter, default_value)

    def visitTask(self, ctx) -> Task:
        task = Task()
        task.name = ctx.STARTS_WITH_LOWER_C_STR().getText()
        task.context = ctx

        self.current_task = task

        if ctx.task_in():
            task.input_parameters = self.visitTask_in(ctx.task_in())
            task.context_dict[IN_KEY] = ctx.task_in()

        for statement_ctx in ctx.taskStatement():
            # reset the current program component for each statement, as this could change during the iteration
            self.current_program_component = task
            self.visitTaskStatement(statement_ctx, task)

        if ctx.task_out():
            task.output_parameters = self.visitTask_out(ctx.task_out())
            task.context_dict[OUT_KEY] = ctx.task_out()

        return task

    def visitTaskStatement(self, ctx, task) -> None:
        if ctx.statement():
            statement = self.visitStatement(ctx.statement())
            task.statements.append(statement)
        elif ctx.constraintStatement():
            if not task.constraints:
                constraints, constraints_string = self.visitConstraintStatement(
                    ctx.constraintStatement()
                )
                task.constraints = constraints
                task.constraints_string = constraints_string
                task.context_dict["Constraints"] = ctx.constraintStatement()
            else:
                # a constraints statement already exists
                error_msg = f"The Task '{task.name}' contains more than one constraint statement."
                self.error_handler.print_error(error_msg, context=ctx)
                return
        elif ctx.eventStatement():
            self.process_event_statement(ctx, task)

    def visitStatement(self, ctx) -> Union[
        TransportOrder,
        MoveOrder,
        ActionOrder,
        Service,
        TaskCall,
        Condition,
        CountingLoop,
        WhileLoop,
        Parallel,
    ]:
        if ctx.transportStatement():
            return self.visitTransportStatement(ctx.transportStatement())
        if ctx.moveStatement():
            return self.visitMoveStatement(ctx.moveStatement())
        if ctx.actionStatement():
            return self.visitActionStatement(ctx.actionStatement())
        else:
            return pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor.visitStatement(self, ctx)

    def visitTransportStatement(self, ctx: PFDLParser.TransportStatementContext) -> TransportOrder:
        transport_order = TransportOrder(
            pickup_tos_names=self.visitTosCollectionStatement(
                ctx.tosCollectionStatement()[0]
            ),  # tos in 'FROM' statement
            delivery_tos_names=self.visitTosCollectionStatement(
                ctx.tosCollectionStatement()[1]
            ),  # tos in 'TO' statement
            context=ctx,
        )
        return transport_order

    def visitTosCollectionStatement(
        self, ctx: PFDLParser.TosCollectionStatementContext
    ) -> List[str]:
        tos_names = []
        for tos_uuid in ctx.STARTS_WITH_LOWER_C_STR():
            tos_names.append(tos_uuid.getText())
        return tos_names

    def visitMoveStatement(self, ctx: PFDLParser.MoveStatementContext) -> MoveOrder:
        return MoveOrder(ctx.STARTS_WITH_LOWER_C_STR().getText(), context=ctx)

    def visitActionStatement(self, ctx: PFDLParser.ActionStatementContext) -> ActionOrder:
        return ActionOrder(ctx.STARTS_WITH_LOWER_C_STR().getText(), context=ctx)

    def visitConstraintStatement(
        self, ctx: PFDLParser.ConstraintStatementContext
    ) -> Tuple[Union[None, str, Dict], str]:
        if ctx.expression():
            constraints = self.visitExpression(ctx.expression())
            return (constraints, ctx.expression().getText())
        else:
            constraints = self.visitJson_object(ctx.json_object())
            return (constraints, ctx.json_object().getText())

    def visitEventStatement(self, ctx: PFDLParser.EventStatementContext) -> None:
        return self.visitExpression(ctx.expression())

    def visitExpression(self, ctx: PFDLParser.ExpressionContext) -> Dict:
        expression = pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor.visitExpression(
            self, ctx
        )

        # it should be a rule call
        if expression is None:
            return self.get_content(ctx.children[0])
        return expression

    def visitOrderStep(
        self, ctx: PFDLParser.OrderStepContext
    ) -> Union[TransportOrderStep, MoveOrderStep, ActionOrderStep]:
        if ctx.transportOrderStep():
            return self.visitTransportOrderStep(ctx.transportOrderStep())
        elif ctx.moveOrderStep():
            return self.visitMoveOrderStep(ctx.moveOrderStep())
        return self.visitActionOrderStep(ctx.actionOrderStep())

    def visitTransportOrderStep(
        self, ctx: PFDLParser.TransportOrderStepContext
    ) -> TransportOrderStep:
        transport_order_step = TransportOrderStep(
            name=ctx.STARTS_WITH_LOWER_C_STR().getText(), context=ctx
        )
        self.current_program_component = transport_order_step
        for statement_ctx in ctx.tosStatement():
            self.visitTosStatement(statement_ctx, transport_order_step)
        return transport_order_step

    def visitTosStatement(
        self, ctx: PFDLParser.TosStatementContext, tos: TransportOrderStep
    ) -> None:
        if ctx.locationStatement():
            self.process_location_statement(ctx, tos)
        if ctx.parameterStatement():
            self.process_parameters_statement(ctx, tos)
        if ctx.eventStatement():
            self.process_event_statement(ctx, tos)
        if ctx.onDoneStatement():
            self.process_on_done_statement(ctx, tos)

    def visitLocationStatement(self, ctx: PFDLParser.LocationStatementContext) -> str:
        self.current_program_component.context_dict["Location"] = ctx
        return ctx.STARTS_WITH_LOWER_C_STR().getText()

    def visitParameterStatement(
        self, ctx: PFDLParser.ParameterStatementContext
    ) -> Union[str, Dict]:
        self.current_program_component.context_dict["Parameter"] = ctx
        if ctx.value():
            return self.visitValue(ctx.value())
        return self.visitJson_object(ctx.json_object())

    def visitOnDoneStatement(self, ctx: PFDLParser.OnDoneStatementContext) -> str:
        return ctx.STARTS_WITH_LOWER_C_STR().getText()

    def visitMoveOrderStep(self, ctx: PFDLParser.MoveOrderStepContext) -> MoveOrderStep:
        move_order_step = MoveOrderStep(name=ctx.STARTS_WITH_LOWER_C_STR().getText(), context=ctx)
        self.current_program_component = move_order_step
        for statement_ctx in ctx.mosStatement():
            self.visitMosStatement(statement_ctx, move_order_step)
        return move_order_step

    def visitMosStatement(self, ctx: PFDLParser.MosStatementContext, mos) -> None:
        if ctx.locationStatement():
            self.process_location_statement(ctx, mos)
        if ctx.eventStatement():
            self.process_event_statement(ctx, mos)
        if ctx.onDoneStatement():
            self.process_on_done_statement(ctx, mos)

    def visitActionOrderStep(self, ctx: PFDLParser.ActionOrderStepContext) -> ActionOrderStep:
        action_order_step = ActionOrderStep(
            name=ctx.STARTS_WITH_LOWER_C_STR().getText(), context=ctx
        )
        self.current_program_component = action_order_step
        for statement_ctx in ctx.aosStatement():
            self.visitAosStatement(statement_ctx, action_order_step)
        return action_order_step

    def visitAosStatement(self, ctx: PFDLParser.AosStatementContext, aos) -> None:
        if ctx.parameterStatement():
            self.process_parameters_statement(ctx, aos)
        if ctx.eventStatement():
            self.process_event_statement(ctx, aos)
        if ctx.onDoneStatement():
            self.process_on_done_statement(ctx, aos)

    def visitJson_object(self, ctx: PFDLParser.Json_objectContext) -> Union[Dict, None]:
        """Returns the parsed JSON object."""
        try:
            return json.loads(ctx.getText())
        except ValueError:
            print(
                "Possible error in the grammar specification! The JSON string to parse"
                + " should be valid at this point of the parsing process."
            )
            raise

    def execute_additional_tasks(self, process: Process) -> None:
        """Runs additional parsing methods with full information."""

        # add primitive structs to the structs dict
        mf_plugin_helpers.add_primitive_structs(process)

        pfdl_scheduler.parser.pfdl_tree_visitor.PFDLTreeVisitor.execute_additional_tasks(
            self, process
        )

        # reprocess ordersteps and orders with full information
        self.reprocess_order_steps(process)

    def reprocess_order_steps(self, process: Process) -> None:
        """Iterates over model objects to set missing data.

        Some data can only be set if we iterate over the generated model objects.
        """
        for task in process.tasks.values():
            self.find_order_steps(task.statements, task, process)

        order_steps = list(process.transport_order_steps.values()) + list(
            process.move_order_steps.values()
        )
        for order_step in order_steps:
            self.add_locations_to_order_step(order_step, process)

    def find_order_steps(self, statements: List, task: Task, process: Process) -> None:
        """Filters statements and finds OrderSteps."""
        for statement in statements:
            if isinstance(statement, self.pfdl_base_classes.get_class("Condition")):
                if statement.passed_stmts:
                    self.find_order_steps(statement.passed_stmts, task, process)
                if statement.failed_stmts:
                    self.find_order_steps(statement.failed_stmts, task, process)
            elif (
                isinstance(
                    statement,
                    (
                        self.pfdl_base_classes.get_class("WhileLoop"),
                        self.pfdl_base_classes.get_class("CountingLoop"),
                    ),
                )
                and statement.statements
            ):
                self.find_order_steps(statement.statements, task, process)

            elif isinstance(statement, TransportOrder):
                # Handle From
                pickup_tos = []
                delivery_tos = []

                for tos_names, tos_instances in [
                    (statement.pickup_tos_names, pickup_tos),
                    (statement.delivery_tos_names, delivery_tos),
                ]:
                    for tos_name in tos_names:
                        order_step = self.get_order_step(
                            tos_name,
                            process.transport_order_steps,
                            task,
                            process,
                            True,
                        )
                        tos_instances.append(order_step)
                statement.pickup_tos = pickup_tos
                statement.delivery_tos = delivery_tos

            elif isinstance(statement, MoveOrder):
                statement.move_order_step = self.get_order_step(
                    statement.move_order_step_name,
                    process.move_order_steps,
                    task,
                    process,
                    False,
                )
                print(statement.move_order_step)
            elif isinstance(statement, ActionOrder):
                statement.action_order_step = self.get_order_step(
                    statement.action_order_step_name,
                    process.action_order_steps,
                    task,
                    process,
                    False,
                )
        return

    def get_order_step(
        self,
        order_step_name: str,
        order_step_dict: Union[
            Dict[str, TransportOrderStep], Dict[str, MoveOrderStep], Dict[str, ActionOrderStep]
        ],
        task: Task,
        process: Process,
        order: Union[TransportOrder, MoveOrder, ActionOrder],
    ) -> Union[TransportOrderStep, MoveOrderStep, ActionOrderStep]:
        """Returns an OrderStep either from the given dict or a newly created one (for locations)."""
        order_step = None

        if order_step_name in order_step_dict:
            order_step = order_step_dict[order_step_name]
        elif isinstance(order, (TransportOrder, MoveOrder)) and order_step_name in task.variables:
            if isinstance(order, TransportOrder):
                order_step = TransportOrderStep("", location_name=order_step_name)
            else:
                order_step = MoveOrderStep("", location_name=order_step_name)

            order_step.context_dict["Location"] = None

            self.add_locations_to_order_step(order_step, process, task.variables)
        else:
            error_msg = (
                f"Task '{task.name}' refers to an unknown " f"OrderStep: '{order_step_name}'."
            )
            self.error_handler.print_error(error_msg, context=task.context)
        return order_step

    def add_locations_to_order_step(
        self,
        order_step: Union[TransportOrderStep, MoveOrderStep],
        process: Process,
        task_variables: Dict[str, Union[str, Array]] = {},
    ) -> None:
        """Tries to find and add the location from the given OrderStep.

        This method will use the location name inside an OrderStep (only for Transport and MoveOrderSteps)
        to find the corresponding Location instance and adds it to the OrderStep. If there is no Location
        instance found, an error will be displayed.
        """
        if (
            order_step.location_name in process.instances
            or order_step.location_name in task_variables
        ):
            if order_step.location_name in task_variables:
                order_step.location = Instance(
                    order_step.location_name,
                    struct_name=task_variables[order_step.location_name],
                )
            else:
                order_step.location = process.instances[order_step.location_name]

            if order_step.location.struct_name != "Location":
                struct = process.structs[order_step.location.struct_name]
                parent_struct_names = helpers.get_parent_struct_names(struct.name, process.structs)[
                    0
                ]
                if "Location" not in parent_struct_names:
                    error_msg = f"The given instance '{order_step.location_name}' is not a Location instance."
                    self.error_handler.print_error(
                        error_msg, context=order_step.context_dict["Location"]
                    )
        else:
            error_msg = f"There is no location instance with the name '{order_step.location_name}'."
            self.error_handler.print_error(error_msg, context=order_step.context)

    def process_event_statement(
        self,
        ctx: Union[
            PFDLParser.TaskStatementContext,
            PFDLParser.TosStatementContext,
            PFDLParser.MosStatementContext,
            PFDLParser.AosStatementContext,
        ],
        program_component: Union[Task, OrderStep],
    ) -> None:
        """
        Visits the event statement and tries to assign the event to the passed program component.

        Throws an error if it is not the only event of this type for the given Task or OrderStep.
        """
        event_ctx = ctx.eventStatement()
        expression = self.visitEventStatement(event_ctx)

        if event_ctx.STARTED_BY():
            if not program_component.started_by_expr:
                program_component.context_dict["StartedBy"] = event_ctx
                program_component.started_by_expr = expression
            else:
                # a started by statement already exists
                error_msg = (
                    f"'{program_component.name}' contains more than one started by statement."
                )
                self.error_handler.print_error(error_msg, context=ctx)
        else:
            if not program_component.finished_by_expr:
                program_component.context_dict["FinishedBy"] = event_ctx
                program_component.finished_by_expr = expression
            else:
                # a finished by statement already exists
                error_msg = (
                    f"'{program_component.name}' contains more than one finished by statement."
                )
                self.error_handler.print_error(error_msg, context=ctx)

    def process_location_statement(
        self,
        ctx: Union[PFDLParser.TosStatementContext, PFDLParser.MosStatementContext],
        order_step: OrderStep,
    ) -> None:
        """
        Tries to visit and assign a Location statement to the current program component.

        Throws an error if it is not the only Location statement for this component.
        """

        if not self.current_program_component.location_name:
            location_name = self.visitLocationStatement(ctx.locationStatement())
            self.current_program_component.location_name = location_name
        else:
            error_msg = f"The OrderStep {order_step.name} contains multiple Location declarations!"
            self.error_handler.print_error(error_msg, context=ctx)

    def process_parameters_statement(
        self,
        ctx: Union[PFDLParser.TosStatementContext, PFDLParser.AosStatementContext],
        order_step: OrderStep,
    ) -> None:
        """
        Tries to visit and assign a Parameters statement to the current program component.

        Throws an error if it is not the only Parameters statement for this component.
        """
        if not self.current_program_component.parameters:
            parameters = self.visitParameterStatement(ctx.parameterStatement())
            self.current_program_component.parameters = parameters
        else:
            error_msg = (
                f"The OrderStep {order_step.name} contains multiple Parameters declarations!"
            )
            self.error_handler.print_error(error_msg, context=ctx)

    def process_on_done_statement(
        self,
        ctx: Union[
            PFDLParser.TosStatementContext,
            PFDLParser.MosStatementContext,
            PFDLParser.AosStatementContext,
        ],
        order_step: OrderStep,
    ) -> None:
        """
        Tries to visit and assign an OnDone statement to the current program component.

        Throws an error if it is not the only OnDone statement for this component.
        """
        if not self.current_program_component.follow_up_task_name:
            follow_up_task_name = self.visitOnDoneStatement(ctx.onDoneStatement())
            self.current_program_component.follow_up_task_name = follow_up_task_name
        else:
            # an OnDone statement already exists
            error_msg = (
                f"The OrderStep '{order_step.name}' contains more than one OnDone statement."
            )
            self.error_handler.print_error(error_msg, context=ctx)
