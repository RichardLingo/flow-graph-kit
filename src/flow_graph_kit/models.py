"""流程图系统 canonical schema 数据模型。

该模块定义 MVP 阶段的核心契约：
- Graph / Node / Port / Edge
- RuntimeToken
- GraphPatch / GraphOp
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class PortDirection(str, Enum):
    """端口方向枚举。

    Attributes:
        INPUT: 输入端口。
        OUTPUT: 输出端口。
    """

    INPUT = "input"
    OUTPUT = "output"


class EdgeKind(str, Enum):
    """连边类型枚举。

    Attributes:
        DATA: 数据流边，用于承载 payload。
        CONTROL: 控制流边，用于触发时序。
    """

    DATA = "data"
    CONTROL = "control"


@dataclass(slots=True)
class Port:
    """端口模型。

    Args:
        uid: 端口唯一标识。
        direction: 端口方向（输入/输出）。
        data_type: 端口数据类型声明（编辑期静态校验基础）。
        schema_id: 可选 schema 标识（精细契约扩展点）。
        metadata: 端口元数据。

    Returns:
        None

    Examples:
        >>> Port(uid="in_a", direction=PortDirection.INPUT, data_type="number")
    """

    uid: str
    direction: PortDirection
    data_type: str
    schema_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Node:
    """节点模型。

    Args:
        uid: 节点唯一标识。
        node_type: 节点类型（对应算子注册键）。
        ports: 节点端口列表。
        content: 节点内容（算子参数或事务配置）。
        metadata: 节点元数据。

    Returns:
        None

    Examples:
        >>> Node(uid="n1", node_type="const", ports=[])
    """

    uid: str
    node_type: str
    ports: list[Port]
    content: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_input_port_ids(self) -> set[str]:
        """获取输入端口 uid 集合。

        Args:
            None

        Returns:
            set[str]: 输入端口 uid 集合。

        Examples:
            >>> node = Node(
            ...     uid="n1",
            ...     node_type="demo",
            ...     ports=[Port(uid="in", direction=PortDirection.INPUT, data_type="number")],
            ... )
            >>> node.get_input_port_ids()
            {'in'}
        """

        return {port.uid for port in self.ports if port.direction == PortDirection.INPUT}

    def get_output_port_ids(self) -> set[str]:
        """获取输出端口 uid 集合。

        Args:
            None

        Returns:
            set[str]: 输出端口 uid 集合。

        Examples:
            >>> node = Node(
            ...     uid="n1",
            ...     node_type="demo",
            ...     ports=[Port(uid="out", direction=PortDirection.OUTPUT, data_type="number")],
            ... )
            >>> node.get_output_port_ids()
            {'out'}
        """

        return {port.uid for port in self.ports if port.direction == PortDirection.OUTPUT}


@dataclass(slots=True)
class Edge:
    """连边模型。

    Args:
        uid: 连边唯一标识。
        source_node_uid: 源节点 uid。
        source_port_uid: 源端口 uid。
        target_node_uid: 目标节点 uid。
        target_port_uid: 目标端口 uid。
        kind: 连边类型（数据流或控制流）。
        metadata: 连边元数据。

    Returns:
        None

    Examples:
        >>> Edge(
        ...     uid="e1",
        ...     source_node_uid="a",
        ...     source_port_uid="out",
        ...     target_node_uid="b",
        ...     target_port_uid="in",
        ... )
    """

    uid: str
    source_node_uid: str
    source_port_uid: str
    target_node_uid: str
    target_port_uid: str
    kind: EdgeKind = EdgeKind.DATA
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeToken:
    """运行时令牌模型。

    Args:
        payload: 令牌承载数据。
        origin: 令牌来源（如节点 uid 或外部输入名）。
        provenance: 追溯链路信息。
        version: 版本标识，用于重放与审计。

    Returns:
        None

    Examples:
        >>> RuntimeToken(payload=1, origin="n1", provenance=["n1"], version="v1")
    """

    payload: Any
    origin: str
    provenance: list[str] = field(default_factory=list)
    version: str = "v1"


@dataclass(slots=True)
class Graph:
    """流程图模型。

    Args:
        uid: 图唯一标识。
        nodes: 节点列表。
        edges: 连边列表。
        metadata: 图元数据。

    Returns:
        None

    Examples:
        >>> Graph(uid="g1", nodes=[], edges=[])
    """

    uid: str
    nodes: list[Node]
    edges: list[Edge]
    metadata: dict[str, Any] = field(default_factory=dict)

    def node_map(self) -> dict[str, Node]:
        """构建节点 uid 到节点对象的映射。

        Args:
            None

        Returns:
            dict[str, Node]: 节点映射。

        Raises:
            ValueError: 当存在重复节点 uid 时抛出。

        Examples:
            >>> graph = Graph(uid="g", nodes=[Node(uid="n", node_type="x", ports=[])], edges=[])
            >>> list(graph.node_map().keys())
            ['n']
        """

        result: dict[str, Node] = {}
        for node in self.nodes:
            if node.uid in result:
                raise ValueError(f"存在重复节点 uid: {node.uid}")
            result[node.uid] = node
        return result

    def to_dict(self) -> dict[str, Any]:
        """将图对象序列化为字典。

        Args:
            None

        Returns:
            dict[str, Any]: 可 JSON 序列化的字典结构。

        Examples:
            >>> graph = Graph(uid="g", nodes=[], edges=[])
            >>> graph.to_dict()["uid"]
            'g'
        """

        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Graph:
        """从字典反序列化为图对象。

        Args:
            data: 图字典数据。

        Returns:
            Graph: 反序列化后的图对象。

        Raises:
            KeyError: 当必要字段缺失时抛出。

        Examples:
            >>> Graph.from_dict({"uid": "g", "nodes": [], "edges": []}).uid
            'g'
        """

        nodes = [
            Node(
                uid=node_data["uid"],
                node_type=node_data["node_type"],
                ports=[
                    Port(
                        uid=port_data["uid"],
                        direction=PortDirection(port_data["direction"]),
                        data_type=port_data["data_type"],
                        schema_id=port_data.get("schema_id"),
                        metadata=port_data.get("metadata", {}),
                    )
                    for port_data in node_data.get("ports", [])
                ],
                content=node_data.get("content", {}),
                metadata=node_data.get("metadata", {}),
            )
            for node_data in data["nodes"]
        ]
        edges = [
            Edge(
                uid=edge_data["uid"],
                source_node_uid=edge_data["source_node_uid"],
                source_port_uid=edge_data["source_port_uid"],
                target_node_uid=edge_data["target_node_uid"],
                target_port_uid=edge_data["target_port_uid"],
                kind=EdgeKind(edge_data.get("kind", EdgeKind.DATA.value)),
                metadata=edge_data.get("metadata", {}),
            )
            for edge_data in data["edges"]
        ]
        return cls(uid=data["uid"], nodes=nodes, edges=edges, metadata=data.get("metadata", {}))


@dataclass(slots=True)
class GraphOp:
    """图操作（Op）模型。

    Args:
        op_type: 操作类型，支持 add_node/remove_node/add_edge/remove_edge。
        payload: 操作负载。

    Returns:
        None

    Examples:
        >>> GraphOp(op_type="add_node", payload={"node": {"uid": "n", "node_type": "x", "ports": []}})
    """

    op_type: str
    payload: dict[str, Any]


@dataclass(slots=True)
class GraphPatch:
    """图补丁模型。

    Args:
        patch_id: 补丁唯一标识。
        timestamp: 补丁时间戳（ISO 字符串或逻辑时钟）。
        ops: 操作序列。
        signature: 可选签名信息。
        metadata: 补丁元数据。

    Returns:
        None

    Examples:
        >>> GraphPatch(patch_id="p1", timestamp="2026-02-27T00:00:00Z", ops=[])
    """

    patch_id: str
    timestamp: str
    ops: list[GraphOp]
    signature: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """将补丁对象序列化为字典。

        Args:
            None

        Returns:
            dict[str, Any]: 可 JSON 序列化字典。

        Examples:
            >>> GraphPatch(patch_id="p", timestamp="t", ops=[]).to_dict()["patch_id"]
            'p'
        """

        return asdict(self)
