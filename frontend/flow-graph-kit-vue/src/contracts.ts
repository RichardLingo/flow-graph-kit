export const CORE_PATCH_OP_TYPES = ['add_node', 'remove_node', 'add_edge', 'remove_edge'] as const;

export const EDITOR_COMMAND_OP_TYPES = [
  'move_node',
  'resize_node',
  'select_node',
  'clear_selection',
  'set_viewport',
] as const;

export type CorePatchOpType = (typeof CORE_PATCH_OP_TYPES)[number];
export type EditorCommandOpType = (typeof EDITOR_COMMAND_OP_TYPES)[number];

export type PortDirection = 'input' | 'output';
export type EdgeKind = 'data' | 'control';

export type Port = {
  uid: string;
  direction: PortDirection;
  data_type: string;
  schema_id?: string | null;
  metadata?: Record<string, unknown>;
};

export type Node = {
  uid: string;
  node_type: string;
  ports: Port[];
  content?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
};

export type Edge = {
  uid: string;
  source_node_uid: string;
  source_port_uid: string;
  target_node_uid: string;
  target_port_uid: string;
  kind?: EdgeKind;
  metadata?: Record<string, unknown>;
};

export type Graph = {
  uid: string;
  nodes: Node[];
  edges: Edge[];
  metadata?: Record<string, unknown>;
};

export type NodeLayout = {
  node_uid: string;
  x: number;
  y: number;
  width: number;
  height: number;
  z_index?: number;
  metadata?: Record<string, unknown>;
};

export type ViewportState = {
  pan_x?: number;
  pan_y?: number;
  scale?: number;
  metadata?: Record<string, unknown>;
};

export type GraphSelection = {
  selected_node_uids?: string[];
  selected_edge_uids?: string[];
  primary_node_uid?: string | null;
  metadata?: Record<string, unknown>;
};

export type GraphEditorDocument = {
  graph: Graph;
  node_layouts?: NodeLayout[];
  viewport?: ViewportState;
  selection?: GraphSelection;
  metadata?: Record<string, unknown>;
};