"""流程图运行时模块。

提供 MVP 阶段的：
- DAG 拓扑排序
- 同步执行器（按拓扑次序执行节点）
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from .models import EdgeKind, Graph, RuntimeToken
from .plugins import OperatorRegistry


def topo_sort(graph: Graph) -> list[str]:
    """对图进行拓扑排序。

    仅将数据流边和控制流边统一视为依赖边，要求图为 DAG。

    Args:
        graph: 流程图对象。

    Returns:
        list[str]: 节点 uid 的拓扑序列。

    Raises:
        ValueError: 当图中存在环时抛出。

    Examples:
        >>> from .models import Node, Edge
        >>> g = Graph(
        ...     uid="g",
        ...     nodes=[Node(uid="a", node_type="x", ports=[]), Node(uid="b", node_type="x", ports=[])],
        ...     edges=[Edge(uid="e", source_node_uid="a", source_port_uid="o", target_node_uid="b", target_port_uid="i")],
        ... )
        >>> topo_sort(g)
        ['a', 'b']
    """

    node_ids = {node.uid for node in graph.nodes}
    indegree = {node_uid: 0 for node_uid in node_ids}
    adjacency: dict[str, list[str]] = defaultdict(list)

    for edge in graph.edges:
        if edge.source_node_uid not in node_ids or edge.target_node_uid not in node_ids:
            raise ValueError(f"连边引用了不存在的节点: {edge.uid}")
        adjacency[edge.source_node_uid].append(edge.target_node_uid)
        indegree[edge.target_node_uid] += 1

    queue = deque(sorted([node_uid for node_uid, degree in indegree.items() if degree == 0]))
    order: list[str] = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for neighbor in adjacency[current]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(node_ids):
        raise ValueError("图中存在环，无法进行拓扑排序")

    return order


def execute_graph(
    graph: Graph,
    registry: OperatorRegistry,
    initial_inputs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, RuntimeToken]]:
    """执行流程图并返回所有节点输出令牌。

    执行规则（MVP 简化版）：
    1. 按拓扑序执行每个节点。
    2. 节点输入由两部分合并：
       - 外部初始输入（`initial_inputs[node_uid]`）
       - 上游 DATA 连边传播的输出值
    3. CONTROL 连边只表示依赖，不承载数据。

    Args:
        graph: 流程图对象。
        registry: 算子注册表。
        initial_inputs: 外部输入，格式为 `{node_uid: {port_uid: value}}`。

    Returns:
        dict[str, dict[str, RuntimeToken]]: 每个节点各输出端口产生的运行时令牌。

    Raises:
        KeyError: 当节点类型无注册算子时抛出。

    Examples:
        >>> from .models import Node, Port, PortDirection
        >>> from .plugins import OperatorRegistry
        >>> g = Graph(uid="g", nodes=[Node(uid="n", node_type="const", ports=[Port(uid="out", direction=PortDirection.OUTPUT, data_type="number")], content={"value": 1})], edges=[])
        >>> registry = OperatorRegistry()
        >>> registry.register("const", lambda inputs, content: {"out": content["value"]})
        >>> execute_graph(g, registry)["n"]["out"].payload
        1
    """

    inputs_by_node: dict[str, dict[str, Any]] = defaultdict(dict)
    outputs_by_node: dict[str, dict[str, RuntimeToken]] = defaultdict(dict)

    if initial_inputs:
        for node_uid, node_inputs in initial_inputs.items():
            inputs_by_node[node_uid].update(node_inputs)

    order = topo_sort(graph)
    node_map = graph.node_map()
    outgoing_edges: dict[str, list] = defaultdict(list)
    for edge in graph.edges:
        outgoing_edges[edge.source_node_uid].append(edge)

    for node_uid in order:
        node = node_map[node_uid]
        operator = registry.get(node.node_type)
        produced_values = operator(dict(inputs_by_node[node_uid]), dict(node.content))

        for port_uid, value in produced_values.items():
            outputs_by_node[node_uid][port_uid] = RuntimeToken(
                payload=value,
                origin=node_uid,
                provenance=[node_uid],
                version="v1",
            )

        for edge in outgoing_edges[node_uid]:
            if edge.kind == EdgeKind.CONTROL:
                continue
            source_token = outputs_by_node[node_uid].get(edge.source_port_uid)
            if source_token is None:
                continue
            inputs_by_node[edge.target_node_uid][edge.target_port_uid] = source_token.payload

    return dict(outputs_by_node)
