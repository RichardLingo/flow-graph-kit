"""MVP 核心能力测试。"""

from flow_graph_kit.models import Edge, Graph, GraphOp, GraphPatch, Node, Port, PortDirection
from flow_graph_kit.patch import apply_patch, diff, invert_patch
from flow_graph_kit.plugins import OperatorRegistry
from flow_graph_kit.runtime import execute_graph, topo_sort


def test_apply_and_invert_patch_roundtrip() -> None:
    """验证补丁应用与逆补丁回滚。

    Args:
        None

    Returns:
        None
    """

    base_graph = Graph(uid="g", nodes=[], edges=[])
    add_node_patch = GraphPatch(
        patch_id="p-add-node",
        timestamp="2026-02-27T12:00:00Z",
        ops=[
            GraphOp(
                op_type="add_node",
                payload={
                    "node": {
                        "uid": "n1",
                        "node_type": "const",
                        "ports": [
                            {
                                "uid": "out",
                                "direction": "output",
                                "data_type": "number",
                            }
                        ],
                        "content": {"value": 1},
                    }
                },
            )
        ],
    )

    patched_graph = apply_patch(base_graph, add_node_patch)
    assert [node.uid for node in patched_graph.nodes] == ["n1"]

    inverse = invert_patch(base_graph, add_node_patch, "p-inverse")
    rolled_back = apply_patch(patched_graph, inverse)
    assert rolled_back.nodes == []
    assert rolled_back.edges == []


def test_diff_should_generate_add_node_and_add_edge() -> None:
    """验证 diff 在新增节点/连边场景下的行为。

    Args:
        None

    Returns:
        None
    """

    old_graph = Graph(uid="g", nodes=[], edges=[])
    new_graph = Graph(
        uid="g",
        nodes=[
            Node(
                uid="n1",
                node_type="const",
                ports=[Port(uid="out", direction=PortDirection.OUTPUT, data_type="number")],
            ),
            Node(
                uid="n2",
                node_type="passthrough",
                ports=[Port(uid="in", direction=PortDirection.INPUT, data_type="number")],
            ),
        ],
        edges=[
            Edge(
                uid="e1",
                source_node_uid="n1",
                source_port_uid="out",
                target_node_uid="n2",
                target_port_uid="in",
            )
        ],
    )

    patch = diff(old_graph, new_graph, patch_id="p-diff", timestamp="2026-02-27T12:00:00Z")
    op_types = {op.op_type for op in patch.ops}
    assert "add_node" in op_types
    assert "add_edge" in op_types


def test_runtime_execute_graph() -> None:
    """验证 DAG 拓扑与执行结果。

    Args:
        None

    Returns:
        None
    """

    graph = Graph(
        uid="g-runtime",
        nodes=[
            Node(
                uid="const_1",
                node_type="const",
                ports=[Port(uid="out", direction=PortDirection.OUTPUT, data_type="number")],
                content={"value": 3},
            ),
            Node(
                uid="double_1",
                node_type="double",
                ports=[
                    Port(uid="in", direction=PortDirection.INPUT, data_type="number"),
                    Port(uid="out", direction=PortDirection.OUTPUT, data_type="number"),
                ],
            ),
        ],
        edges=[
            Edge(
                uid="e1",
                source_node_uid="const_1",
                source_port_uid="out",
                target_node_uid="double_1",
                target_port_uid="in",
            )
        ],
    )

    assert topo_sort(graph) == ["const_1", "double_1"]

    registry = OperatorRegistry()
    registry.register("const", lambda _inputs, content: {"out": content["value"]})
    registry.register("double", lambda inputs, _content: {"out": inputs["in"] * 2})

    outputs = execute_graph(graph, registry)
    assert outputs["const_1"]["out"].payload == 3
    assert outputs["double_1"]["out"].payload == 6
