import { computed, shallowRef } from 'vue';

import type { GraphEditorDocument } from './contracts';
import {
  clearSelectionInDocument,
  connectNodesWithDefaultPorts,
  createNodeLayoutMap,
  moveNodeLayoutInDocument,
  resizeNodeLayoutInDocument,
  selectSingleNodeInDocument,
} from './document';

export function useGraphEditorDocument(initialDocument: GraphEditorDocument) {
  const document = shallowRef<GraphEditorDocument>(initialDocument);

  const layoutMap = computed(() => createNodeLayoutMap(document.value));

  const setDocument = (next: GraphEditorDocument) => {
    document.value = next;
  };

  const moveNode = (nodeUid: string, position: { x: number; y: number }) => {
    document.value = moveNodeLayoutInDocument(document.value, nodeUid, position);
  };

  const resizeNode = (nodeUid: string, size: { width: number; height: number }) => {
    document.value = resizeNodeLayoutInDocument(document.value, nodeUid, size);
  };

  const selectSingleNode = (nodeUid: string | null) => {
    document.value = selectSingleNodeInDocument(document.value, nodeUid);
  };

  const clearSelection = () => {
    document.value = clearSelectionInDocument(document.value);
  };

  const connectNodes = (edgeUid: string, sourceNodeUid: string, targetNodeUid: string) => {
    document.value = connectNodesWithDefaultPorts(document.value, { edgeUid, sourceNodeUid, targetNodeUid });
  };

  return {
    document,
    layoutMap,
    setDocument,
    moveNode,
    resizeNode,
    selectSingleNode,
    clearSelection,
    connectNodes,
  };
}