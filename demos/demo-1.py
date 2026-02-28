"""最小示例：演示 flow_graph_kit 的基础使用方式。

本示例展示：
1. 如何定义节点与连边构建 DAG。
2. 如何注册算子（Operator）。
3. 如何执行图并读取输出令牌。
"""

from flow_graph_kit import (
    Edge,
    Graph,
    Node,
    OperatorRegistry,
    Port,
    PortDirection,
    execute_graph,
)


def 构建示例流程图() -> Graph:
    """构建一个最小可执行流程图。

    图结构：
    - `const_1(out)` -> `double_1(in)`

    Args:
        None

    Returns:
        Graph: 构建完成的示例图对象。

    Raises:
        None

    Examples:
        >>> graph = 构建示例流程图()
        >>> graph.uid
        'demo_graph_1'
    """

    常量节点 = Node(
        uid="const_1",
        node_type="const",
        ports=[Port(uid="out", direction=PortDirection.OUTPUT, data_type="number")],
        content={"value": 21},
    )
    翻倍节点 = Node(
        uid="double_1",
        node_type="double",
        ports=[
            Port(uid="in", direction=PortDirection.INPUT, data_type="number"),
            Port(uid="out", direction=PortDirection.OUTPUT, data_type="number"),
        ],
    )
    数据连边 = Edge(
        uid="edge_1",
        source_node_uid="const_1",
        source_port_uid="out",
        target_node_uid="double_1",
        target_port_uid="in",
    )
    return Graph(uid="demo_graph_1", nodes=[常量节点, 翻倍节点], edges=[数据连边])


def 构建算子注册表() -> OperatorRegistry:
    """构建并返回示例算子注册表。

    Args:
        None

    Returns:
        OperatorRegistry: 已注册 `const` 与 `double` 算子的注册表。

    Raises:
        ValueError: 当重复注册同名算子时抛出。

    Examples:
        >>> registry = 构建算子注册表()
        >>> 'const' in registry
        True
    """

    注册表 = OperatorRegistry()
    注册表.register("const", lambda _inputs, content: {"out": content["value"]})
    注册表.register("double", lambda inputs, _content: {"out": inputs["in"] * 2})
    return 注册表


def main() -> None:
    """运行最小示例并打印执行结果。

    Args:
        None

    Returns:
        None

    Raises:
        KeyError: 当算子缺失时抛出。

    Examples:
        >>> main()
    """

    示例图 = 构建示例流程图()
    注册表 = 构建算子注册表()
    输出结果 = execute_graph(示例图, 注册表)

    最终值 = 输出结果["double_1"]["out"].payload
    print("demo-1 执行完成")
    print(f"double_1.out = {最终值}")


if __name__ == "__main__":
    main()
