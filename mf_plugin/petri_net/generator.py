# Copyright The MF-Plugin Contributors
#
# Licensed under the MIT License.
# For details on the licensing terms, see the LICENSE file.
# SPDX-License-Identifier: MIT

"""This file contains plugin code to overwrite the PFDL class PetriNetGenerator."""

# standard libraries
import uuid
from typing import Dict, List, OrderedDict, Tuple, Union

# 3rd party libraries
from snakes import plugins

# local sources
## PFDL base sources
from pfdl_scheduler.pfdl_base_classes import PFDLBaseClasses
import pfdl_scheduler.plugins
from pfdl_scheduler.api.task_api import TaskAPI
from pfdl_scheduler.model import process
from pfdl_scheduler.model.task_call import TaskCall
from pfdl_scheduler.petri_net.generator import Node, create_place, create_transition

## MF-Plugin sources
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.api.order_api import OrderAPI
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.api.order_step_api import OrderStepAPI
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.transport_order import TransportOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.action_order import ActionOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.model.move_order import MoveOrder
from pfdl_scheduler.plugins.mf_plugin.mf_plugin.petri_net.callbacks import PetriNetCallbacks
from pfdl_scheduler.plugins.plugin_loader import base_class


plugins.load(["labels", "gv", "clusters"], "snakes.nets", "nets")
from nets import PetriNet, Value, Cluster


@base_class("PetriNetGenerator")
class PetriNetGenerator(pfdl_scheduler.petri_net.generator.PetriNetGenerator):
    """
        Generates a Petri Net from a given Process object which corresponds to a PFDL file.

    Attributes:
        path_for_image: The path where the image of the generated Petri Net is saved.
        net: The snakes Petri Net instance.
        draw_net: A boolean indiciating whether the net should be drawn.
        tasks: A dict representing the Tasks of the given Process object.
        transition_dict: A dict for mapping the UUIDs of the Transitions to their behavior.
        place_dict: A dict for mapping the service uuid to the place name.
        task_started_uuid: The uuid of the 'Task started' place.
        callbacks: A PetriNetCallbacks instance representing functions called while execution.
        generate_test_ids: A boolean indicating if test ids (counting from 0) should be generated.
        used_in_extension: A boolean indicating if the Generator is used within the extension.
        tree: The Node representing the mainTask and therefore the tree including all program components.
        file_name: The filename of the petri net image.
        order_step_test_id_counter: A counter for the ordersteps when test ids are generated, counting from 0.
        uuids_per_task: A dict containing the uuids of each Task and all uuids of order steps and statements that correspond to that Task.
        task_apis: A list containing APIs for all Tasks in the program.
        orders: A list containing APIs for all orders in the program.
        order_steps: A list containing APIs for all order steps in the program.
    """

    def __init__(
        self,
        path_for_image: str = "",
        used_in_extension: bool = False,
        generate_test_ids: bool = False,
        draw_net: bool = True,
        file_name: str = "petri_net",
        pfdl_base_classes: PFDLBaseClasses = PFDLBaseClasses(),
    ) -> None:
        """Initialize the object.

        Args:
            path_for_image: The path where the image of the generated Petri Net is saved.
            used_in_extension: A boolean indicating if the Generator is used within the extension.
            generate_test_ids: A boolean indicating if test ids (counting from 0) should be generated.
            draw_net: A boolean indicating if the petri net should be drawn.
            file_name: The desired filename of the petri net image.
        """
        pfdl_scheduler.petri_net.generator.PetriNetGenerator.__init__(
            self,
            path_for_image,
            used_in_extension,
            generate_test_ids,
            draw_net,
            file_name,
            pfdl_base_classes,
        )
        self.order_step_test_id_counter = -1
        self.transition_dict: OrderedDict = OrderedDict()
        self.uuids_per_task: Dict[str, Dict[str, Union[str, Dict]]] = {}
        self.task_apis: List[TaskAPI] = []
        self.orders: List[OrderAPI] = []
        self.order_steps: List[OrderStepAPI] = []
        self.callbacks = PetriNetCallbacks()  # using MF-Plugin implementation of PetriNetCallbacks

    def handle_other_statements(
        self,
        statement,
        task_context: TaskAPI,
        first_transition_uuid: str,
        second_transition_uuid: str,
        node: Node,
        in_loop: bool = False,
    ) -> Tuple[str]:
        """Generates Petri Net components for MF-Plugin specific components,
        namely TransportOrders, MoveOrders and ActionOrders.

        Returns:
            A list of uuids of the last transition in the respective component.
        """
        # create a new dict for an unknown task
        if task_context.uuid not in self.uuids_per_task:
            self.uuids_per_task[task_context.uuid] = {}

        if isinstance(statement, TransportOrder):
            last_transition_uuids = self.generate_transport_order(
                statement,
                task_context,
                first_transition_uuid,
                second_transition_uuid,
                node,
                in_loop,
            )
        elif isinstance(statement, MoveOrder):
            last_transition_uuids = self.generate_move_order(
                statement,
                task_context,
                first_transition_uuid,
                second_transition_uuid,
                node,
                in_loop,
            )
        else:
            last_transition_uuids = self.generate_action_order(
                statement,
                task_context,
                first_transition_uuid,
                second_transition_uuid,
                node,
                in_loop,
            )

        if not isinstance(last_transition_uuids, List):
            last_transition_uuids = [last_transition_uuids]

        return last_transition_uuids

    def generate_petri_net(self, process: process) -> PetriNet:
        """
        Overwrites the PFDL PetriNetGenerator generate_petri_net function to assign the process to the generator.

        Returns:
            A PetriNet instance representing the generated net.
        """
        self.process = process

        return pfdl_scheduler.petri_net.generator.PetriNetGenerator.generate_petri_net(
            self, process
        )

    def generate_statements(
        self,
        task_context: TaskAPI,
        statements: List,
        first_connection_uuid: str,
        last_connection_uuid: str,
        node: Node,
        in_loop: bool = False,
    ) -> List[str]:
        """Generate Petri Net components for each statement in the given Task

        Iterate over the statements of the given Tasks and generate the corresponding
        Petri Net components. Connect the individual components with each other via a
        transition.

        Returns:
            The uuids of the last connections (transitions).
        """
        if not task_context in self.task_apis:
            # the production task
            self.task_apis.append(task_context)
        return pfdl_scheduler.petri_net.generator.PetriNetGenerator.generate_statements(
            self,
            task_context,
            statements,
            first_connection_uuid,
            last_connection_uuid,
            node,
            in_loop,
        )

    def generate_task_call(
        self,
        task_call: TaskCall,
        task_context: TaskAPI,
        first_transition_uuid: str,
        second_transition_uuid: str,
        node: Node,
        in_loop: bool = False,
    ) -> List[str]:
        """Generates a Task Call in the Petri Net.

        Returns:
            a list containing the uuids of the last transitions of the TaskCall petri net component.
        """
        called_task = self.tasks[task_call.name]

        group_uuid = str(uuid.uuid4())
        task_node = Node(group_uuid, task_call.name, node)

        task_cluster = Cluster([])
        node.cluster.add_child(task_cluster)
        task_node.cluster = task_cluster

        if called_task.started_by_expr is not None:
            started_by_uuid, _, start_transition_uuid = self.generate_started_by(
                first_transition_uuid, task_node, node.group_uuid, True
            )

            uuids, context = self.generate_pfdl_task_call(
                task_call,
                task_context,
                start_transition_uuid,
                second_transition_uuid,
                task_node,
                in_loop,
            )
            self.uuids_per_task[context.uuid]["started_by"] = started_by_uuid
            self.add_callback(
                first_transition_uuid,
                self.callbacks.started_by,
                context,
            )

        else:
            uuids, context = self.generate_pfdl_task_call(
                task_call,
                task_context,
                first_transition_uuid,
                second_transition_uuid,
                task_node,
                in_loop,
            )

        return uuids

    def generate_pfdl_task_call(
        self,
        task_call: TaskCall,
        task_context: TaskAPI,
        first_transition_uuid: str,
        second_transition_uuid: str,
        task_node: Node,
        in_loop: bool = False,
    ) -> Tuple[List[str], TaskAPI]:
        """Generates the Petri Net components for a Task Call.

        Returns:
            A tuple containing
                - a list of the uuids of the last transitions of the TaskCall petri net component.
                - a TaskAPI representing the new task context
        """
        called_task = self.tasks[task_call.name]
        new_task_context = TaskAPI(called_task, task_context, task_call=task_call, in_loop=in_loop)

        # create a new dict for an unknown task
        self.uuids_per_task[new_task_context.uuid] = {}
        self.task_apis.append(new_task_context)

        # Order for callbacks important: Task starts before statement and finishes after
        self.add_callback(first_transition_uuid, self.callbacks.task_started, new_task_context)
        if called_task.finished_by_expr is not None:
            # create a new transition between first_transition and second_transition
            transition_before_finished_by = create_transition("", "", self.net, task_node)
            task_node.cluster.add_node(transition_before_finished_by)

            # generate task statements, connect the last nodes to the newly created transition
            last_connection_uuids = self.generate_statements(
                new_task_context,
                called_task.statements,
                first_transition_uuid,
                transition_before_finished_by,
                task_node,
                in_loop,
            )

            for last_connection_uuid in last_connection_uuids:
                self.add_callback(
                    last_connection_uuid, self.callbacks.finished_by, new_task_context
                )

            # generate the finished_by statement
            (
                waiting_for_finished_by_uuid,
                finished_by_uuid,
            ) = self.generate_finished_by_for_task(
                transition_before_finished_by,
                second_transition_uuid,
                task_node,
                task_node.group_uuid,
            )

            last_connection_uuids = [waiting_for_finished_by_uuid, finished_by_uuid]
            self.uuids_per_task[new_task_context.uuid]["finished_by"] = finished_by_uuid
            self.add_callback(
                second_transition_uuid, self.callbacks.task_finished, new_task_context
            )
        else:
            last_connection_uuids = self.generate_statements(
                new_task_context,
                called_task.statements,
                first_transition_uuid,
                second_transition_uuid,
                task_node,
                in_loop,
            )
            for last_connection_uuid in last_connection_uuids:
                self.add_callback(
                    last_connection_uuid, self.callbacks.task_finished, new_task_context
                )

        return last_connection_uuids, new_task_context

    def generate_transport_order(
        self,
        transport_order: TransportOrder,
        task_api: TaskAPI,
        first_connection: str,
        second_connection: str,
        node: Node,
        in_loop: bool = False,
    ) -> str:
        """Generate the Petri Net components for a TransportOrder.

        Returns:
            The uuid of the TransportOrder finished place.
        """
        group_uuid = str(uuid.uuid4())
        transport_order_node = Node(group_uuid, "Transport Order", node)

        transport_started_uuid = create_place(
            "Transport \n started", self.net, transport_order_node
        )
        # the first transition node of the transport
        branch_transition_uuid = create_transition("", "", self.net, transport_order_node)
        sync_transition_uuid = create_transition("", "", self.net, transport_order_node)
        self.net.add_output(transport_started_uuid, first_connection, Value(1))
        self.net.add_input(transport_started_uuid, branch_transition_uuid, Value(1))

        order_api = OrderAPI(transport_order, task_api, in_loop)
        self.orders.append(order_api)
        self.add_callback(first_connection, self.callbacks.order_started, order_api)

        # setup clustering
        cluster = Cluster([transport_started_uuid, branch_transition_uuid, sync_transition_uuid])
        node.cluster.add_child(cluster)
        transport_order_node.cluster = cluster

        last_pickup_tos_transitions = []
        for pickup_tos in transport_order.pickup_tos:
            last_pickup_tos_transitions.append(
                self.handle_transport_order_step(
                    pickup_tos,
                    order_api,
                    task_api,
                    transport_order_node,
                    branch_transition_uuid,
                    sync_transition_uuid,
                    second_connection,
                    in_loop,
                    False,
                )
            )

        last_delivery_tos_transitions = []
        for delivery_tos in transport_order.delivery_tos:
            last_delivery_tos_transitions.append(
                self.handle_transport_order_step(
                    delivery_tos,
                    order_api,
                    task_api,
                    transport_order_node,
                    sync_transition_uuid,
                    second_connection,
                    second_connection,
                    in_loop,
                    True,
                )
            )

        return last_delivery_tos_transitions

    def handle_transport_order_step(
        self,
        transport_order_step,
        order_api,
        task_api,
        transport_order_node,
        first_transition_uuid,
        second_transition_uuid,
        final_transition_uuid,
        in_loop,
        is_delivery,
    ) -> str:
        """Execute methods to handle a TransportOrderStep, consisting of
        - the generation of the corresponding Petri Net component
        - the registration of callbacks
        - the generation of a possible OnDone Task

        Returns:
            The uuid of the TransportOrderStep finished place.
        """
        tos_api = OrderStepAPI(transport_order_step, order_api)
        if self.order_step_test_id_counter != -1:
            tos_api.uuid = str(self.order_step_test_id_counter)
            self.order_step_test_id_counter = self.order_step_test_id_counter + 1

        self.order_steps.append(tos_api)
        uuids, has_follow_up_task = self.generate_transport_order_step(
            tos_api, task_api, transport_order_node
        )

        tos_started_uuid, tos_finished_uuid, last_transition_uuid = uuids

        # add the callback for the first transition of this transport order (depending on whether this is connected to a started_by or a normal tos node)
        if transport_order_step.started_by_expr is not None:
            self.add_callback(
                first_transition_uuid,
                self.callbacks.started_by,
                task_api,
                tos_api,
            )
        else:
            self.add_callback(
                first_transition_uuid,
                self.callbacks.waiting_for_move,
                tos_api,
                task_api,
            )

        self.net.add_output(tos_started_uuid, first_transition_uuid, Value(1))
        self.net.add_input(tos_finished_uuid, second_transition_uuid, Value(1))

        second_transition_uuid = last_transition_uuid

        if is_delivery:
            # order_finished_callback, only relevant for delivery order steps
            self.add_callback(second_transition_uuid, self.callbacks.order_finished, order_api)

        if has_follow_up_task:
            # create a new task call for the onDone task of the current transport order step
            self.generate_on_done(
                tos_api,
                task_api,
                second_transition_uuid,
                final_transition_uuid,
                transport_order_node,
                in_loop,
            )

        return last_transition_uuid

    def generate_transport_order_step(
        self,
        tos_api: OrderStepAPI,
        task_api: TaskAPI,
        node: Node,
    ) -> Tuple[Tuple[str, str, str], bool]:
        """Generate the Petri Net components for a TransportOrderStep.

        Returns:
            A tuple consisting of
                - another tuple that holds the uuids of the TransportOrderStep started and finished place
                    and the uuid of the last transition.
                - a boolean indicating whether this TransportOrderStep contains an OnDone statement or not
        """
        group_uuid = str(uuid.uuid4())
        # the clustering node
        tos_node = Node(group_uuid, tos_api.order_step.name, node)

        tos = tos_api.order_step

        tos_started_uuid = create_place(tos.name + "\n started", self.net, tos_node)
        tos_finished_uuid = create_place(tos.name + "\n finished", self.net, tos_node)

        first_transition_uuid = create_transition("", "", self.net, tos_node)
        moved_to_location_uuid = create_place(
            f"Moved to \n {tos.location_name}", self.net, tos_node
        )

        # define which nodes are connected with the transition
        self.net.add_input(tos_started_uuid, first_transition_uuid, Value(1))
        self.net.add_input(moved_to_location_uuid, first_transition_uuid, Value(1))

        self.add_callback(first_transition_uuid, self.callbacks.moved_to_location, tos_api)

        action_executed_uuid = ""
        # there might only be one transition node in this cluster
        last_transition_uuid = first_transition_uuid

        # setup clustering
        cluster = Cluster(
            [
                tos_started_uuid,
                tos_finished_uuid,
                moved_to_location_uuid,
                last_transition_uuid,
            ]
        )
        node.cluster.add_child(cluster)
        tos_node.cluster = cluster

        # add more nodes to the TransportOrderStep cluster
        waiting_for_action_uuid = create_place("Waiting for action", self.net, tos_node)
        action_executed_uuid = create_place("Action executed", self.net, tos_node)
        last_transition_uuid = create_transition("", "", self.net, tos_node)

        tos_node.cluster.add_node(waiting_for_action_uuid)
        tos_node.cluster.add_node(action_executed_uuid)
        tos_node.cluster.add_node(last_transition_uuid)

        self.net.add_output(waiting_for_action_uuid, first_transition_uuid, Value(1))
        self.net.add_input(waiting_for_action_uuid, last_transition_uuid, Value(1))
        self.net.add_input(action_executed_uuid, last_transition_uuid, Value(1))

        self.add_callback(
            first_transition_uuid,
            self.callbacks.waiting_for_action,
            tos_api,
            task_api,
        )
        self.add_callback(last_transition_uuid, self.callbacks.action_executed, tos_api)

        # check if there are StartedBy or FinishedBy statements and if so, generate components
        started_by_uuid = ""
        finished_by_uuid = ""
        if tos.started_by_expr is not None:
            started_by_uuid, tos_started_uuid, start_transition_uuid = self.generate_started_by(
                tos_started_uuid, tos_node, group_uuid, False
            )

            # add a waiting_for_move callback for the transition between the started_by expression and the first "actual" transport order step node
            self.add_callback(
                start_transition_uuid,
                self.callbacks.waiting_for_move,
                tos_api,
                task_api,
            )

        if tos.finished_by_expr is not None:
            (
                finished_by_uuid,
                finished_by_transition_uuid,
            ) = self.generate_finished_by_for_order_step(
                last_transition_uuid, tos_finished_uuid, tos_node, group_uuid
            )

            self.add_callback(last_transition_uuid, self.callbacks.finished_by, task_api, tos_api)

            last_transition_uuid = finished_by_transition_uuid  # update last transition
        else:
            self.net.add_output(tos_finished_uuid, last_transition_uuid, Value(1))

        self.uuids_per_task[task_api.uuid][tos_api.uuid] = {
            "moved_to_location": moved_to_location_uuid,
            "action_executed": action_executed_uuid,
            "started_by": started_by_uuid,
            "finished_by": finished_by_uuid,
        }

        # tell the parent transport order wether it has to call a follow up task
        has_follow_up_task = tos.follow_up_task_name != ""

        return (tos_started_uuid, tos_finished_uuid, last_transition_uuid), has_follow_up_task

    def generate_move_order(
        self,
        move_order: MoveOrder,
        task_api: TaskAPI,
        first_connection: str,
        second_connection: str,
        node: Node,
        in_loop: bool = False,
    ) -> str:
        """Generate the Petri Net components for a MoveOrder.

        Returns:
            The uuid of the MoveOrder finished place.
        """
        group_uuid = str(uuid.uuid4())
        move_order_node = Node(group_uuid, "Move Order", node)

        mos = self.process.move_order_steps[move_order.move_order_step_name]

        order_api = OrderAPI(move_order, task_api, in_loop)
        mos_api = OrderStepAPI(mos, order_api)

        self.add_callback(first_connection, self.callbacks.order_started, order_api)

        if self.order_step_test_id_counter != -1:
            mos_api.uuid = str(self.order_step_test_id_counter)
            self.order_step_test_id_counter = self.order_step_test_id_counter + 1

        self.orders.append(order_api)
        self.order_steps.append(mos_api)

        move_started_uuid = create_place("Move \n started", self.net, move_order_node)
        first_transition_uuid = create_transition("", "", self.net, move_order_node)

        self.net.add_input(move_started_uuid, first_transition_uuid, Value(1))
        self.net.add_output(move_started_uuid, first_connection, Value(1))

        # setup clustering
        cluster = Cluster([move_started_uuid, first_transition_uuid])
        node.cluster.add_child(cluster)
        move_order_node.cluster = cluster

        uuids, has_follow_up_task = self.generate_move_order_step(
            mos_api, task_api, move_order_node
        )

        mos_started_uuid, mos_finished_uuid, mos_last_transition_uuid = uuids

        if mos.started_by_expr is not None:
            self.add_callback(first_transition_uuid, self.callbacks.started_by, task_api, mos_api)
        else:
            self.add_callback(
                first_transition_uuid,
                self.callbacks.waiting_for_move,
                mos_api,
                task_api,
            )

        self.net.add_output(mos_started_uuid, first_transition_uuid, Value(1))

        self.add_callback(mos_last_transition_uuid, self.callbacks.order_finished, order_api)

        self.net.add_input(mos_finished_uuid, second_connection, Value(1))

        if has_follow_up_task:
            # create a new task call for the onDone task of the current transport order step
            self.generate_on_done(
                mos_api,
                task_api,
                mos_last_transition_uuid,
                second_connection,
                move_order_node,
                in_loop,
            )
        return mos_last_transition_uuid

    def generate_move_order_step(
        self,
        mos_api: OrderStepAPI,
        task_api: TaskAPI,
        node: Node,
    ) -> Tuple[Tuple[str, str, str], bool]:
        """Generate the Petri Net components for a MoveOrderStep.

        Returns:
            A tuple consisting of
                - another tuple that holds the uuids of the MoveOrderStep started and finished place
                    and the uuid of the last transition.
                - a boolean indicating whether this MoveOrderStep contains an OnDone statement or not
        """
        mos = mos_api.order_step

        group_uuid = str(uuid.uuid4())
        mos_node = Node(group_uuid, mos.name, node)

        mos_started_uuid = create_place(mos.name + "\n started", self.net, mos_node)
        mos_finished_uuid = create_place(mos.name + "\n finished", self.net, mos_node)

        first_transition_uuid = create_transition("", "", self.net, mos_node)
        moved_to_location_uuid = create_place(
            f"Moved to \n {mos.location_name}", self.net, mos_node
        )

        # setup clustering
        cluster = Cluster(
            [
                mos_started_uuid,
                mos_finished_uuid,
                first_transition_uuid,
                moved_to_location_uuid,
            ]
        )
        node.cluster.add_child(cluster)
        mos_node.cluster = cluster

        self.net.add_input(mos_started_uuid, first_transition_uuid, Value(1))
        self.net.add_input(moved_to_location_uuid, first_transition_uuid, Value(1))

        self.add_callback(first_transition_uuid, self.callbacks.moved_to_location, mos_api)

        last_transition_uuid = first_transition_uuid

        # check if there are StartedBy or FinishedBy statements and if so, generate components
        started_by_uuid = ""
        finished_by_uuid = ""
        if mos.started_by_expr is not None:
            started_by_uuid, mos_started_uuid, start_transition_uuid = self.generate_started_by(
                mos_started_uuid, mos_node, group_uuid, False
            )

            self.add_callback(
                start_transition_uuid,
                self.callbacks.waiting_for_move,
                mos_api,
                task_api,
            )

        if mos.finished_by_expr is not None:
            (
                finished_by_uuid,
                finished_by_transition_uuid,
            ) = self.generate_finished_by_for_order_step(
                last_transition_uuid, mos_finished_uuid, mos_node, group_uuid
            )

            self.add_callback(last_transition_uuid, self.callbacks.finished_by, task_api, mos_api)

            last_transition_uuid = finished_by_transition_uuid  # update last transition
        else:
            self.net.add_output(mos_finished_uuid, last_transition_uuid, Value(1))

        self.uuids_per_task[task_api.uuid][mos_api.uuid] = {
            "moved_to_location": moved_to_location_uuid,
            "started_by": started_by_uuid,
            "finished_by": finished_by_uuid,
        }

        has_follow_up_task = mos.follow_up_task_name != ""

        return (mos_started_uuid, mos_finished_uuid, last_transition_uuid), has_follow_up_task

    def generate_action_order(
        self,
        action_order: ActionOrder,
        task_api: TaskAPI,
        first_connection: str,
        second_connection: str,
        node: Node,
        in_loop: bool = False,
    ) -> Tuple[str, str]:
        """Generate the Petri Net components for an ActionOrder.

        Returns:
            The uuid of the ActionOrder finished place.
        """
        group_uuid = str(uuid.uuid4())
        action_order_node = Node(group_uuid, "Action Order", node)

        aos = self.process.action_order_steps[action_order.action_order_step_name]

        order_api = OrderAPI(action_order, task_api, in_loop)
        aos_api = OrderStepAPI(aos, order_api)

        self.add_callback(first_connection, self.callbacks.order_started, order_api)

        if self.order_step_test_id_counter != -1:
            aos_api.uuid = str(self.order_step_test_id_counter)
            self.order_step_test_id_counter = self.order_step_test_id_counter + 1

        self.orders.append(order_api)
        self.order_steps.append(aos_api)

        action_started_uuid = create_place("Action \n started", self.net, action_order_node)
        first_transition_uuid = create_transition("", "", self.net, action_order_node)

        # setup clustering
        cluster = Cluster([action_started_uuid, first_transition_uuid])
        node.cluster.add_child(cluster)
        action_order_node.cluster = cluster

        self.net.add_input(action_started_uuid, first_transition_uuid, Value(1))
        self.net.add_output(action_started_uuid, first_connection, Value(1))

        uuids, has_follow_up_task = self.generate_action_order_step(
            aos_api, task_api, action_order_node
        )

        aos_started_uuid, aos_finished_uuid, aos_last_transition_uuid = uuids

        if aos.started_by_expr is not None:
            self.add_callback(first_transition_uuid, self.callbacks.started_by, task_api, aos_api)
        else:
            self.add_callback(
                first_transition_uuid,
                self.callbacks.waiting_for_action,
                aos_api,
                task_api,
            )

        self.net.add_output(aos_started_uuid, first_transition_uuid, Value(1))

        self.add_callback(aos_last_transition_uuid, self.callbacks.order_finished, order_api)

        self.net.add_input(aos_finished_uuid, second_connection, Value(1))

        if has_follow_up_task:
            # create a new task call for the onDone task of the current transport order step
            self.generate_on_done(
                aos_api,
                task_api,
                aos_last_transition_uuid,
                second_connection,
                action_order_node,
                in_loop,
            )

        return aos_last_transition_uuid

    def generate_action_order_step(
        self,
        aos_api: OrderStepAPI,
        task_api: TaskAPI,
        node: Node,
    ) -> Tuple[Tuple[str, str, str], bool]:
        """Generate the Petri Net components for an ActionOrderStep.

        Returns:
            A tuple consisting of
                - another tuple that holds the uuids of the ActionOrderStep started and finished place
                    and the uuid of the last transition.
                - a boolean indicating whether this ActionOrderStep contains an OnDone statement or not
        """
        aos = aos_api.order_step

        group_uuid = str(uuid.uuid4())
        aos_node = Node(group_uuid, aos.name, node)

        # create places for petri net
        aos_started_uuid = create_place(aos.name + "\n started", self.net, aos_node)
        aos_finished_uuid = create_place(aos.name + "\n finished", self.net, aos_node)

        first_transition_uuid = create_transition("", "", self.net, aos_node)
        action_executed_uuid = create_place("Action executed", self.net, aos_node)

        # setup clustering
        cluster = Cluster(
            [
                aos_started_uuid,
                aos_finished_uuid,
                first_transition_uuid,
                action_executed_uuid,
            ]
        )
        node.cluster.add_child(cluster)
        aos_node.cluster = cluster

        # add action order step to petri net
        self.net.add_input(aos_started_uuid, first_transition_uuid, Value(1))
        self.net.add_input(action_executed_uuid, first_transition_uuid, Value(1))

        # update net when the action was executed
        self.add_callback(first_transition_uuid, self.callbacks.action_executed, aos_api)

        # currently only one transition node for this statement
        last_transition_uuid = first_transition_uuid

        # check if there are StartedBy or FinishedBy statements and if so, generate components
        started_by_uuid = ""
        finished_by_uuid = ""
        if aos.started_by_expr is not None:
            # insert startedBy component before the aos_started_uuid place in the petri net
            started_by_uuid, aos_started_uuid, start_transition_uuid = self.generate_started_by(
                aos_started_uuid, aos_node, group_uuid, False
            )
            self.add_callback(
                start_transition_uuid,
                self.callbacks.waiting_for_action,
                aos_api,
                task_api,
            )

        if aos.finished_by_expr is not None:
            # insert finishedBy component after the last transition and before the aos_finished place in the petri net
            (
                finished_by_uuid,
                finished_by_transition_uuid,
            ) = self.generate_finished_by_for_order_step(
                last_transition_uuid, aos_finished_uuid, aos_node, group_uuid
            )

            self.add_callback(last_transition_uuid, self.callbacks.finished_by, task_api, aos_api)

            last_transition_uuid = finished_by_transition_uuid  # update last transition
        else:
            self.net.add_output(aos_finished_uuid, last_transition_uuid, Value(1))

        self.uuids_per_task[task_api.uuid][aos_api.uuid] = {
            "action_executed": action_executed_uuid,
            "started_by": started_by_uuid,
            "finished_by": finished_by_uuid,
        }

        has_follow_up_task = aos.follow_up_task_name != ""
        return (aos_started_uuid, aos_finished_uuid, last_transition_uuid), has_follow_up_task

    def generate_on_done(
        self,
        order_step_api: OrderStepAPI,
        task_api: TaskAPI,
        first_transition: str,
        second_transition: str,
        node: Node,
        in_loop: bool = False,
    ) -> Tuple[List[str], TaskAPI]:
        """
        Generates the Petri Net components for an OnDone TaskCall.

        Returns:
            A tuple containing
                - a list of the uuids of the last transitions of the TaskCall petri net component.
                - a TaskAPI representing the new task context
        """

        task_call = TaskCall(order_step_api.order_step.follow_up_task_name)

        return self.generate_task_call(
            task_call, task_api, first_transition, second_transition, node, in_loop
        )

    def generate_started_by(
        self,
        start_place_or_transition: str,
        node: Node,
        group_uuid: str,
        generate_for_task: bool,
    ) -> Tuple[str, str, str]:
        """
        Generate a StartedBy expression for a Task or an OrderStep (indicated by generate_for_task)

        Returns: the UUIDs of the newly created place "StartedBy satisfied", the place from where to continue
                    after the StartedBy was satisfied and the transition within the StartedBy.
        """
        waiting_for_started_by_uuid = create_place("Waiting for \n StartedBy", self.net, node)
        started_by_uuid = create_place("StartedBy \n satisfied", self.net, node)
        start_transition_uuid = create_transition("", "", self.net, node)
        self.net.add_input(started_by_uuid, start_transition_uuid, Value(1))
        self.net.add_input(waiting_for_started_by_uuid, start_transition_uuid, Value(1))

        if generate_for_task:
            # when called from a task, we only have access to the previous transition
            self.net.add_output(waiting_for_started_by_uuid, start_place_or_transition, Value(1))
        else:
            # when called from an OrderStep, we have access to the place that is reached after the StartedBy expression is met
            self.net.add_output(start_place_or_transition, start_transition_uuid, Value(1))
            start_place_or_transition = waiting_for_started_by_uuid  # the orderstep starting point

        node.cluster.add_node(waiting_for_started_by_uuid)
        node.cluster.add_node(started_by_uuid)
        node.cluster.add_node(start_transition_uuid)

        return (started_by_uuid, start_place_or_transition, start_transition_uuid)

    def generate_finished_by_for_task(
        self,
        transition_before_finished_by_uuid: str,
        finished_by_transition_uuid: str,
        node: Node,
        group_uuid: str,
    ) -> Tuple[str, str]:
        """
        Generate a FinishedBy expression for a Task. The next place after the FinishedBy is currently unknown.

        Returns: the UUIDs of the newly created places for 'Waiting for FinishedBy' and 'FinishedBy satisfied'
        """
        waiting_for_finished_by_uuid = create_place("Waiting for \n FinishedBy", self.net, node)
        finished_by_uuid = create_place("FinishedBy \n satisfied", self.net, node)

        self.net.add_input(finished_by_uuid, finished_by_transition_uuid, Value(1))
        self.net.add_input(waiting_for_finished_by_uuid, finished_by_transition_uuid, Value(1))
        self.net.add_output(
            waiting_for_finished_by_uuid, transition_before_finished_by_uuid, Value(1)
        )

        node.cluster.add_node(waiting_for_finished_by_uuid)
        node.cluster.add_node(finished_by_uuid)

        return (waiting_for_finished_by_uuid, finished_by_uuid)

    def generate_finished_by_for_order_step(
        self,
        transition_before_finished_by_uuid: str,
        place_after_finished_by_uuid: str,
        node: Node,
        group_uuid: str,
    ) -> Tuple[str, str]:
        """
        Generate a FinishedBy expression for an OrderStep. The next place after the FinishedBy is known.

        Returns: the UUIDs of the newly created place for 'FinishedBy satisfied' and the transition
        """
        waiting_for_finished_by_uuid = create_place("Waiting for \n FinishedBy", self.net, node)
        finished_by_uuid = create_place("FinishedBy \n satisfied", self.net, node)

        # we know the place after the FinishedBy expression is met, so create a new transition and connect it to that place
        finished_by_transition_uuid = create_transition("", "", self.net, node)
        self.net.add_input(finished_by_uuid, finished_by_transition_uuid, Value(1))
        self.net.add_input(waiting_for_finished_by_uuid, finished_by_transition_uuid, Value(1))
        self.net.add_output(
            waiting_for_finished_by_uuid, transition_before_finished_by_uuid, Value(1)
        )
        self.net.add_output(place_after_finished_by_uuid, finished_by_transition_uuid, Value(1))

        node.cluster.add_node(waiting_for_finished_by_uuid)
        node.cluster.add_node(finished_by_uuid)
        node.cluster.add_node(finished_by_transition_uuid)

        return (finished_by_uuid, finished_by_transition_uuid)

    def parse_expression(self, expression: Dict) -> str:
        """Overwrites the PFDL PetriNetGenerator parse_expression function to take care of Rules in Conditions.

        Returns:
            The content of the expression as a formatted string.
        """
        if isinstance(expression, Tuple):
            expression = str(expression)
        return pfdl_scheduler.petri_net.generator.PetriNetGenerator.parse_expression(
            self, expression
        )
