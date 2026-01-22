import { useCallback, useEffect, useState } from 'react';
import {
    ReactFlow,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    type Edge,
    type Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { parseScenario, getStepLabel, getStepDescription, type Scenario, type ScenarioStep } from '@/lib/yamlParser';
import { ScenarioNode, type ScenarioNodeData } from '@/components/flow/ScenarioNode';
import { FlowLegend } from '@/components/flow/FlowLegend';
import { StepDetailPanel } from '@/components/flow/StepDetailPanel';

interface ScenarioFlowPreviewProps {
    yaml: string | null;
}

const nodeTypes = {
    scenario: ScenarioNode,
};

export function ScenarioFlowPreview({ yaml }: ScenarioFlowPreviewProps) {
    const [parseError, setParseError] = useState<string | null>(null);
    const [selectedStep, setSelectedStep] = useState<ScenarioStep | null>(null);

    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

    const parseAndRender = useCallback((yamlInput: string) => {
        const result = parseScenario(yamlInput);

        if (result.error) {
            const errorMsg = result.error.line
                ? `Line ${result.error.line}: ${result.error.message}`
                : result.error.message;
            setParseError(errorMsg);
            setNodes([]);
            setEdges([]);
            return;
        }

        setParseError(null);
        if (result.scenario) {
            const { nodes: newNodes, edges: newEdges } = generateFlowElements(result.scenario);
            setNodes(newNodes);
            setEdges(newEdges);
        }
    }, [setEdges, setNodes]);

    useEffect(() => {
        if (!yaml) {
            setParseError(null);
            setNodes([]);
            setEdges([]);
            return;
        }
        parseAndRender(yaml);
    }, [yaml, parseAndRender, setEdges, setNodes]);

    const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
        const data = node.data as ScenarioNodeData;
        if (data?.step) {
            setSelectedStep(data.step);
        }
    }, []);

    const handlePaneClick = useCallback(() => {
        setSelectedStep(null);
    }, []);

    if (!yaml) {
        return (
            <div className="h-full glass rounded-2xl p-6 flex items-center justify-center text-sm text-slate-500">
                Select a scenario to preview the flowchart.
            </div>
        );
    }

    return (
        <div className="h-full glass rounded-2xl overflow-hidden relative">
            {parseError && (
                <div className="absolute top-4 left-4 right-4 z-20 rounded-xl bg-rose-500/10 border border-rose-500/20 px-4 py-2">
                    <p className="text-xs font-mono text-rose-400">{parseError}</p>
                </div>
            )}
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={handleNodeClick}
                onPaneClick={handlePaneClick}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                minZoom={0.3}
                maxZoom={2}
                proOptions={{ hideAttribution: true }}
            >
                <Background color="#334155" gap={20} size={1} />
                <Controls
                    className="!bg-slate-900/80 !border-white/10 !rounded-lg !shadow-xl"
                    showInteractive={false}
                />
                <MiniMap
                    className="!bg-slate-900/80 !border-white/10 !rounded-lg"
                    nodeColor={(node) => {
                        const data = node.data as ScenarioNodeData | undefined;
                        const type = data?.step?.type;
                        switch (type) {
                            case 'http': return '#06b6d4';
                            case 'wait': return '#f59e0b';
                            case 'assert': return '#10b981';
                            case 'branch': return '#a855f7';
                            default: return '#64748b';
                        }
                    }}
                    maskColor="rgba(0,0,0,0.7)"
                />
            </ReactFlow>
            <FlowLegend />
            <StepDetailPanel step={selectedStep} onClose={() => setSelectedStep(null)} />
        </div>
    );
}

function generateFlowElements(scenario: Scenario): { nodes: Node[]; edges: Edge[] } {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    const nodeSpacingY = 100;
    const startY = 50;

    scenario.flow.forEach((step, index) => {
        const nodeId = `step-${index}`;

        const nodeData: ScenarioNodeData = {
            step,
            label: getStepLabel(step),
            description: getStepDescription(step),
            index,
        };

        nodes.push({
            id: nodeId,
            type: 'scenario',
            position: { x: 0, y: startY + index * nodeSpacingY },
            data: nodeData,
        });

        if (index > 0) {
            edges.push({
                id: `edge-${index - 1}-${index}`,
                source: `step-${index - 1}`,
                target: nodeId,
                type: 'smoothstep',
                style: { stroke: '#475569', strokeWidth: 2 },
                animated: false,
            });
        }
    });

    const maxWidth = 280;
    nodes.forEach((node) => {
        node.position.x = -maxWidth / 2;
    });

    return { nodes, edges };
}
