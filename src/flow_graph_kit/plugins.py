"""算子注册表模块。

用于管理 `node_type -> 可调用算子` 的映射关系。
"""

from __future__ import annotations

from typing import Any, Callable

OperatorCallable = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


class OperatorRegistry:
    """算子注册表。

    约定算子签名为：
    `operator(inputs: dict[str, Any], content: dict[str, Any]) -> dict[str, Any]`

    其中返回字典键为输出端口 uid，值为该端口输出数据。

    Examples:
        >>> registry = OperatorRegistry()
        >>> registry.register("const", lambda inputs, content: {"out": content["value"]})
        >>> "const" in registry
        True
    """

    def __init__(self) -> None:
        """初始化空注册表。

        Args:
            None

        Returns:
            None
        """

        self._operators: dict[str, OperatorCallable] = {}

    def register(self, node_type: str, operator: OperatorCallable) -> None:
        """注册算子。

        Args:
            node_type: 节点类型。
            operator: 算子可调用对象。

        Returns:
            None

        Raises:
            ValueError: 当 node_type 已存在时抛出。
        """

        if node_type in self._operators:
            raise ValueError(f"算子已注册: {node_type}")
        self._operators[node_type] = operator

    def get(self, node_type: str) -> OperatorCallable:
        """获取算子。

        Args:
            node_type: 节点类型。

        Returns:
            OperatorCallable: 算子函数。

        Raises:
            KeyError: 当 node_type 未注册时抛出。
        """

        if node_type not in self._operators:
            raise KeyError(f"未注册算子: {node_type}")
        return self._operators[node_type]

    def __contains__(self, node_type: str) -> bool:
        """判断是否存在某节点类型的算子。

        Args:
            node_type: 节点类型。

        Returns:
            bool: 是否已注册。
        """

        return node_type in self._operators
