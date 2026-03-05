"""图补丁（GraphPatch）能力实现。

该模块提供：
- apply_patch：将补丁应用到图
- invert_patch：生成逆补丁
- diff：在两个图之间生成最小变更补丁（节点/连边增删）
"""

from __future__ import annotations

from copy import deepcopy

from .models import Edge, Graph, GraphOp, GraphPatch, Node


def apply_patch(graph: Graph, patch: GraphPatch) -> Graph:
    """应用补丁并返回新图。

    Args:
        graph: 原始图对象。
        patch: 要应用的图补丁。

    Returns:
        Graph: 应用补丁后的新图对象。

    Raises:
        ValueError: 当操作类型不支持，或引用对象不存在/重复时抛出。

    Examples:
        >>> from .models import GraphPatch, GraphOp
        >>> base = Graph(uid="g", nodes=[], edges=[])
        >>> patch = GraphPatch(
        ...     patch_id="p1",
        ...     timestamp="2026-02-27T00:00:00Z",
        ...     ops=[GraphOp(op_type="add_node", payload={"node": {"uid": "n1", "node_type": "const", "ports": []}})],
        ... )
        >>> apply_patch(base, patch).nodes[0].uid
        'n1'
    """

    next_graph = deepcopy(graph)
    for op in patch.ops:
        if op.op_type == "add_node":
            node = Node.from_dict(op.payload["node"]) if hasattr(Node, "from_dict") else _node_from_dict(op.payload["node"])
            if any(existing.uid == node.uid for existing in next_graph.nodes):
                raise ValueError(f"节点已存在: {node.uid}")
            next_graph.nodes.append(node)
        elif op.op_type == "remove_node":
            node_uid = op.payload["node_uid"]
            if not any(existing.uid == node_uid for existing in next_graph.nodes):
                raise ValueError(f"节点不存在: {node_uid}")
            next_graph.nodes = [node for node in next_graph.nodes if node.uid != node_uid]
            next_graph.edges = [
                edge
                for edge in next_graph.edges
                if edge.source_node_uid != node_uid and edge.target_node_uid != node_uid
            ]
        elif op.op_type == "add_edge":
            edge = _edge_from_dict(op.payload["edge"])
            if any(existing.uid == edge.uid for existing in next_graph.edges):
                raise ValueError(f"连边已存在: {edge.uid}")
            next_graph.edges.append(edge)
        elif op.op_type == "remove_edge":
            edge_uid = op.payload["edge_uid"]
            if not any(existing.uid == edge_uid for existing in next_graph.edges):
                raise ValueError(f"连边不存在: {edge_uid}")
            next_graph.edges = [edge for edge in next_graph.edges if edge.uid != edge_uid]
        else:
            raise ValueError(f"不支持的操作类型: {op.op_type}")
    return next_graph


def invert_patch(graph: Graph, patch: GraphPatch, inverted_patch_id: str) -> GraphPatch:
    """基于原图和补丁生成逆补丁。

    Args:
        graph: 应用 patch 前的原图。
        patch: 原补丁。
        inverted_patch_id: 逆补丁标识。

    Returns:
        GraphPatch: 可回滚原补丁的逆补丁。

    Raises:
        ValueError: 当操作类型不支持时抛出。

    Examples:
        >>> base = Graph(uid="g", nodes=[], edges=[])
        >>> p = GraphPatch(patch_id="p", timestamp="t", ops=[])
        >>> invert_patch(base, p, "inv").patch_id
        'inv'
    """

    current_graph = deepcopy(graph)
    inverse_ops: list[GraphOp] = []

    for op in patch.ops:
        if op.op_type == "add_node":
            node_data = op.payload["node"]
            inverse_ops.insert(0, GraphOp(op_type="remove_node", payload={"node_uid": node_data["uid"]}))
        elif op.op_type == "remove_node":
            node_uid = op.payload["node_uid"]
            target_node = next((node for node in current_graph.nodes if node.uid == node_uid), None)
            if target_node is not None:
                inverse_ops.insert(0, GraphOp(op_type="add_node", payload={"node": _node_to_dict(target_node)}))
        elif op.op_type == "add_edge":
            edge_data = op.payload["edge"]
            inverse_ops.insert(0, GraphOp(op_type="remove_edge", payload={"edge_uid": edge_data["uid"]}))
        elif op.op_type == "remove_edge":
            edge_uid = op.payload["edge_uid"]
            target_edge = next((edge for edge in current_graph.edges if edge.uid == edge_uid), None)
            if target_edge is not None:
                inverse_ops.insert(0, GraphOp(op_type="add_edge", payload={"edge": _edge_to_dict(target_edge)}))
        else:
            raise ValueError(f"不支持的操作类型: {op.op_type}")

        current_graph = apply_patch(
            current_graph,
            GraphPatch(
                patch_id=f"{patch.patch_id}-step",
                timestamp=patch.timestamp,
                ops=[op],
            ),
        )

    return GraphPatch(
        patch_id=inverted_patch_id,
        timestamp=patch.timestamp,
        ops=inverse_ops,
        metadata={"inverted_from": patch.patch_id},
    )


def diff(old_graph: Graph, new_graph: Graph, patch_id: str, timestamp: str) -> GraphPatch:
    """根据新旧图生成补丁。

    Args:
        old_graph: 旧图。
        new_graph: 新图。
        patch_id: 生成补丁的标识。
        timestamp: 补丁时间戳。

    Returns:
        GraphPatch: 从 old_graph 迁移到 new_graph 的补丁。

    Examples:
        >>> old = Graph(uid="g", nodes=[], edges=[])
        >>> new = Graph(uid="g", nodes=[Node(uid="n", node_type="x", ports=[])], edges=[])
        >>> diff(old, new, "p", "t").ops[0].op_type
        'add_node'
    """

    old_nodes = {node.uid: node for node in old_graph.nodes}
    new_nodes = {node.uid: node for node in new_graph.nodes}
    old_edges = {edge.uid: edge for edge in old_graph.edges}
    new_edges = {edge.uid: edge for edge in new_graph.edges}

    ops: list[GraphOp] = []

    for edge_uid in old_edges.keys() - new_edges.keys():
        ops.append(GraphOp(op_type="remove_edge", payload={"edge_uid": edge_uid}))
    for node_uid in old_nodes.keys() - new_nodes.keys():
        ops.append(GraphOp(op_type="remove_node", payload={"node_uid": node_uid}))

    for node_uid in new_nodes.keys() - old_nodes.keys():
        ops.append(GraphOp(op_type="add_node", payload={"node": _node_to_dict(new_nodes[node_uid])}))
    for edge_uid in new_edges.keys() - old_edges.keys():
        ops.append(GraphOp(op_type="add_edge", payload={"edge": _edge_to_dict(new_edges[edge_uid])}))

    return GraphPatch(patch_id=patch_id, timestamp=timestamp, ops=ops)


def _node_from_dict(data: dict) -> Node:
    """从字典构建 Node。

    Args:
        data: 节点字典。

    Returns:
        Node: 节点对象。
    """

    graph = Graph.from_dict({"uid": "_temp", "nodes": [data], "edges": []})
    return graph.nodes[0]


def _edge_from_dict(data: dict) -> Edge:
    """从字典构建 Edge。

    Args:
        data: 连边字典。

    Returns:
        Edge: 连边对象。
    """

    graph = Graph.from_dict({"uid": "_temp", "nodes": [], "edges": [data]})
    return graph.edges[0]


def _node_to_dict(node: Node) -> dict:
    """将 Node 转换为字典。

    Args:
        node: 节点对象。

    Returns:
        dict: 节点字典。
    """

    return {
        "uid": node.uid,
        "node_type": node.node_type,
        "ports": [
            {
                "uid": port.uid,
                "direction": port.direction.value,
                "data_type": port.data_type,
                "schema_id": port.schema_id,
                "metadata": port.metadata,
            }
            for port in node.ports
        ],
        "content": node.content,
        "metadata": node.metadata,
    }


def _edge_to_dict(edge: Edge) -> dict:
    """将 Edge 转换为字典。

    Args:
        edge: 连边对象。

    Returns:
        dict: 连边字典。
    """

    return {
        "uid": edge.uid,
        "source_node_uid": edge.source_node_uid,
        "source_port_uid": edge.source_port_uid,
        "target_node_uid": edge.target_node_uid,
        "target_port_uid": edge.target_port_uid,
        "kind": edge.kind.value,
        "metadata": edge.metadata,
    }
