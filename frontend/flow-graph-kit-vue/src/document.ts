import type { Edge, GraphEditorDocument, GraphSelection, NodeLayout, ViewportState } from './contracts';

type Vec2 = { x: number; y: number };
type Size = { width: number; height: number };

const cloneSelection = (selection: GraphSelection | undefined): Required<GraphSelection> => ({
  selected_node_uids: [...(selection?.selected_node_uids ?? [])],
  selected_edge_uids: [...(selection?.selected_edge_uids ?? [])],
  primary_node_uid: selection?.primary_node_uid ?? null,
  metadata: { ...(selection?.metadata ?? {}) },
});

const cloneViewport = (viewport: ViewportState | undefined): Required<ViewportState> => ({
  pan_x: viewport?.pan_x ?? 0,
  pan_y: viewport?.pan_y ?? 0,
  scale: viewport?.scale ?? 1,
  metadata: { ...(viewport?.metadata ?? {}) },
});

const cloneLayout = (layout: NodeLayout): NodeLayout => ({
  ...layout,
  z_index: layout.z_index ?? 0,
  metadata: { ...(layout.metadata ?? {}) },
});

const cloneEdge = (edge: Edge): Edge => ({
  ...edge,
  kind: edge.kind ?? 'data',
  metadata: { ...(edge.metadata ?? {}) },
});

export function cloneGraphEditorDocument(document: GraphEditorDocument): GraphEditorDocument {
  return {
    graph: {
      ...document.graph,
      metadata: { ...(document.graph.metadata ?? {}) },
      nodes: document.graph.nodes.map((node) => ({
        ...node,
        metadata: { ...(node.metadata ?? {}) },
        content: { ...(node.content ?? {}) },
        ports: node.ports.map((port) => ({ ...port, metadata: { ...(port.metadata ?? {}) } })),
      })),
      edges: document.graph.edges.map(cloneEdge),
    },
    node_layouts: (document.node_layouts ?? []).map(cloneLayout),
    viewport: cloneViewport(document.viewport),
    selection: cloneSelection(document.selection),
    metadata: { ...(document.metadata ?? {}) },
  };
}

export function createNodeLayoutMap(document: GraphEditorDocument): Map<string, NodeLayout> {
  const result = new Map<string, NodeLayout>();
  for (const layout of document.node_layouts ?? []) {
    result.set(layout.node_uid, layout);
  }
  return result;
}

export function moveNodeLayoutInDocument(document: GraphEditorDocument, nodeUid: string, position: Vec2): GraphEditorDocument {
  const next = cloneGraphEditorDocument(document);
  next.node_layouts = (next.node_layouts ?? []).map((layout) =>
    layout.node_uid === nodeUid ? { ...layout, x: position.x, y: position.y } : layout,
  );
  return next;
}

export function resizeNodeLayoutInDocument(document: GraphEditorDocument, nodeUid: string, size: Size): GraphEditorDocument {
  const next = cloneGraphEditorDocument(document);
  next.node_layouts = (next.node_layouts ?? []).map((layout) =>
    layout.node_uid === nodeUid ? { ...layout, width: size.width, height: size.height } : layout,
  );
  return next;
}

export function selectSingleNodeInDocument(document: GraphEditorDocument, nodeUid: string | null): GraphEditorDocument {
  const next = cloneGraphEditorDocument(document);
  next.selection = {
    ...cloneSelection(next.selection),
    selected_node_uids: nodeUid ? [nodeUid] : [],
    selected_edge_uids: [],
    primary_node_uid: nodeUid,
  };
  return next;
}

export function clearSelectionInDocument(document: GraphEditorDocument): GraphEditorDocument {
  return selectSingleNodeInDocument(document, null);
}

export function connectNodesWithDefaultPorts(document: GraphEditorDocument, args: { edgeUid: string; sourceNodeUid: string; targetNodeUid: string }): GraphEditorDocument {
  const next = cloneGraphEditorDocument(document);
  const exists = next.graph.edges.some(
    (edge) =>
      edge.source_node_uid === args.sourceNodeUid &&
      edge.target_node_uid === args.targetNodeUid &&
      edge.source_port_uid === 'out' &&
      edge.target_port_uid === 'in',
  );
  if (exists) {
    return next;
  }
  next.graph.edges = [
    ...next.graph.edges,
    {
      uid: args.edgeUid,
      source_node_uid: args.sourceNodeUid,
      source_port_uid: 'out',
      target_node_uid: args.targetNodeUid,
      target_port_uid: 'in',
      kind: 'data',
      metadata: {},
    },
  ];
  return next;
}