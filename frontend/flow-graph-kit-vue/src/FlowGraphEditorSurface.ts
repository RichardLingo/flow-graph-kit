import { computed, defineComponent, h, ref, type PropType } from 'vue';
import {
  Viewport2D,
  ViewportBusinessCanvasShell,
  useViewportHostBridge,
  type ViewportHostBridge,
} from 'viewport-2d-kit/vue';
import type { ViewBox, Viewport2DCamera } from 'viewport-2d-kit/core';

import type { Edge, GraphEditorDocument, Node, NodeLayout } from './contracts';

export type FlowGraphEditorSurfaceSlotArgs = {
  camera: Viewport2DCamera;
  bridge: ViewportHostBridge;
  document: GraphEditorDocument;
  nodeMap: Map<string, Node>;
  layoutMap: Map<string, NodeLayout>;
};

const EDGE_LAYER_STYLE = {
  position: 'absolute',
  inset: 0,
  width: '100%',
  height: '100%',
  pointerEvents: 'none',
  overflow: 'visible',
} as const;

const DEFAULT_EDGE_STYLE = {
  fill: 'none',
  stroke: 'var(--main-ui-accent, #2563eb)',
  strokeWidth: 2,
} as const;

const centerOf = (layout: NodeLayout) => ({ x: layout.x + layout.width / 2, y: layout.y + layout.height / 2 });

const buildDefaultEdgePath = (edge: Edge, layoutMap: Map<string, NodeLayout>): string => {
  const source = layoutMap.get(edge.source_node_uid);
  const target = layoutMap.get(edge.target_node_uid);
  if (!source || !target) {
    return '';
  }
  const from = centerOf(source);
  const to = centerOf(target);
  const dx = Math.abs(to.x - from.x);
  return `M ${from.x} ${from.y} C ${from.x + dx * 0.42} ${from.y}, ${to.x - dx * 0.42} ${to.y}, ${to.x} ${to.y}`;
};

export const FlowGraphEditorSurface = defineComponent({
  name: 'FlowGraphEditorSurface',
  props: {
    document: {
      type: Object as PropType<GraphEditorDocument>,
      required: true,
    },
    viewBox: {
      type: Object as PropType<ViewBox>,
      required: true,
    },
    background: {
      type: String,
      default: '#fbfbfd',
    },
    leftPanelWidth: {
      type: [Number, String] as PropType<number | string>,
      default: 210,
    },
    rightPanelWidth: {
      type: [Number, String] as PropType<number | string>,
      default: 320,
    },
    toolbarHeight: {
      type: [Number, String] as PropType<number | string>,
      default: 36,
    },
    paddingPx: {
      type: Number,
      default: 80,
    },
    minScaleFactor: {
      type: Number,
      default: 0.08,
    },
    maxScaleFactor: {
      type: Number,
      default: 64,
    },
    wheelZoomSpeed: {
      type: Number,
      default: 0.0028,
    },
    wheelPanSpeed: {
      type: Number,
      default: 1,
    },
    holdToPanKey: {
      type: String as PropType<'space' | 'none'>,
      default: 'space',
    },
  },
  setup(props, { slots }) {
    const hostRef = ref<HTMLDivElement | null>(null);
    const bridge = useViewportHostBridge(
      hostRef as unknown as Parameters<typeof useViewportHostBridge>[0],
      props.viewBox,
    );

    const layoutMap = computed(() => {
      const map = new Map<string, NodeLayout>();
      for (const layout of props.document.node_layouts ?? []) {
        map.set(layout.node_uid, layout);
      }
      return map;
    });

    const nodeMap = computed(() => {
      const map = new Map<string, Node>();
      for (const node of props.document.graph.nodes) {
        map.set(node.uid, node);
      }
      return map;
    });

    return () =>
      h(
        ViewportBusinessCanvasShell,
        {
          leftPanelWidth: props.leftPanelWidth,
          rightPanelWidth: props.rightPanelWidth,
          toolbarHeight: props.toolbarHeight,
        },
        {
          left: () => slots.left?.(),
          toolbarLeading: () => slots.toolbarLeading?.(),
          toolbarCenter: () => slots.toolbarCenter?.(),
          toolbarTrailing: () => slots.toolbarTrailing?.(),
          right: () => slots.right?.(),
          default: () => [
            h(
              'div',
              {
                ref: hostRef,
                style: { minWidth: 0, minHeight: 0, position: 'relative', width: '100%', height: '100%' },
              },
              [
                h(
                  Viewport2D,
                  {
                    viewBox: props.viewBox,
                    background: props.background,
                    paddingPx: props.paddingPx,
                    minScaleFactor: props.minScaleFactor,
                    maxScaleFactor: props.maxScaleFactor,
                    wheelZoomSpeed: props.wheelZoomSpeed,
                    wheelPanSpeed: props.wheelPanSpeed,
                    holdToPanKey: props.holdToPanKey,
                    style: { width: '100%', height: '100%' },
                  },
                  {
                    default: ({ camera }: { camera: Viewport2DCamera }) => [
                      h(
                        'div',
                        {
                          style: {
                            ...bridge.worldStyle.value,
                            position: 'absolute',
                            left: 0,
                            top: 0,
                          },
                        },
                        [
                          h(
                            'svg',
                            {
                              style: EDGE_LAYER_STYLE,
                              viewBox: bridge.viewBoxText.value,
                              'aria-hidden': 'true',
                            },
                            props.document.graph.edges.map((edge) =>
                              h('path', {
                                key: edge.uid,
                                style: DEFAULT_EDGE_STYLE,
                                d: buildDefaultEdgePath(edge, layoutMap.value),
                              }),
                            ),
                          ),
                          ...(slots.world?.({
                            camera,
                            bridge,
                            document: props.document,
                            nodeMap: nodeMap.value,
                            layoutMap: layoutMap.value,
                          }) ?? []),
                        ],
                      ),
                    ],
                  },
                ),
              ],
            ),
          ],
        },
      );
  },
});

export default FlowGraphEditorSurface;