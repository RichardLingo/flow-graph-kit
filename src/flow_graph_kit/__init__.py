"""flow_graph_kit 包入口。

该模块对外暴露最小可行版本（MVP）的核心类型与能力：
- 规范数据模型（Graph / Node / Port / Edge / RuntimeToken / GraphPatch）
- 图补丁能力（apply_patch / invert_patch / diff）
- 运行时能力（topo_sort / execute_graph）
"""

from .models import (
    Edge,
    EdgeKind,
    Graph,
    GraphOp,
    GraphPatch,
    Node,
    Port,
    PortDirection,
    RuntimeToken,
)
from .patch import apply_patch, diff, invert_patch
from .plugins import OperatorRegistry
from .runtime import execute_graph, topo_sort

__all__ = [
    "PortDirection",
    "EdgeKind",
    "Port",
    "Node",
    "Edge",
    "Graph",
    "RuntimeToken",
    "GraphOp",
    "GraphPatch",
    "apply_patch",
    "invert_patch",
    "diff",
    "OperatorRegistry",
    "topo_sort",
    "execute_graph",
]
