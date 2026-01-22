/**
 * ScenarioVisualizerPage
 *
 * Visual flowchart rendering of YAML scenarios with clickable steps.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import {
    ReactFlow,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    type Node,
    type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { parseScenario, getStepLabel, getStepDescription, type Scenario, type ScenarioStep } from '@/lib/yamlParser';
import { ScenarioNode, type ScenarioNodeData } from '@/components/flow/ScenarioNode';
import { FlowLegend } from '@/components/flow/FlowLegend';
import { StepDetailPanel } from '@/components/flow/StepDetailPanel';

// Sample YAML for initial state
const SAMPLE_YAML = `# Sample Scenario
id: sample-flow
description: A simple API test flow

flow:
  - type: http
    name: get_users
    service: api
    method: GET
    path: /api/users
    extract:
      first_user_id: "$.data[0].id"

  - type: assert
    name: verify_success
    expect:
      status_code: 200

  - type: http
    name: get_user_details
    service: api
    method: GET
    path: "/api/users/{{first_user_id}}"
    extract:
      user_name: "$.name"

  - type: wait
    name: wait_for_processing
    service: api
    path: "/api/jobs/123"
    interval_seconds: 1
    timeout_seconds: 30
    expect:
      jsonpath: "$.status"
      equals: "complete"

  - type: assert
    name: final_check
    expect:
      jsonpath: "$.success"
      equals: "true"
`;

const nodeTypes = {
    scenario: ScenarioNode,
};

export function ScenarioVisualizerPage() {
    const [yamlInput, setYamlInput] = useState(SAMPLE_YAML);
    const [parseError, setParseError] = useState<string | null>(null);
    const [selectedStep, setSelectedStep] = useState<ScenarioStep | null>(null);
    const [showYamlPanel, setShowYamlPanel] = useState(true);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

    // Parse YAML and generate flow
    const parseAndRender = useCallback((yaml: string) => {
        const result = parseScenario(yaml);

        if (result.error) {
            const errorMsg = result.error.line
                ? `Line ${result.error.line}: ${result.error.message}`
                : result.error.message;
            setParseError(errorMsg);
            return;
        }

        setParseError(null);
        if (result.scenario) {
            const { nodes: newNodes, edges: newEdges } = generateFlowElements(result.scenario);
            setNodes(newNodes);
            setEdges(newEdges);
        }
    }, [setNodes, setEdges]);

    // Initial parse
    useEffect(() => {
        parseAndRender(yamlInput);
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // Handle YAML input changes with debounce
    const handleYamlChange = useCallback((value: string) => {
        setYamlInput(value);
        // Debounce parsing
        const timer = setTimeout(() => parseAndRender(value), 200);
        return () => clearTimeout(timer);
    }, [parseAndRender]);

    // Handle file upload
    const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const content = event.target?.result as string;
            setYamlInput(content);
            parseAndRender(content);
        };
        reader.readAsText(file);
    }, [parseAndRender]);

    // Handle node click
    const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
        const data = node.data as ScenarioNodeData;
        if (data?.step) {
            setSelectedStep(data.step);
        }
    }, []);

    // Handle pane click (deselect)
    const handlePaneClick = useCallback(() => {
        setSelectedStep(null);
    }, []);

    return (
        <div className="h-[calc(100vh-120px)] flex flex-col gap-6 animate-in fade-in duration-700">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-4xl font-bold tracking-tight text-white glow-cyan mb-2">
                        Scenario Visualizer
                    </h1>
                    <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">
                        YAML → Flowchart Rendering
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setShowYamlPanel(!showYamlPanel)}
                        className={`px-4 py-2 rounded-xl glass text-xs font-bold uppercase tracking-widest transition-all ${showYamlPanel ? 'text-cyan-400' : 'text-slate-500'
                            }`}
                    >
                        {showYamlPanel ? 'Hide Editor' : 'Show Editor'}
                    </button>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".yaml,.yml"
                        onChange={handleFileUpload}
                        className="hidden"
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="px-4 py-2 rounded-xl glass glass-hover text-cyan-400 text-xs font-bold uppercase tracking-widest flex items-center gap-2"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                        </svg>
                        Upload YAML
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex gap-4 min-h-0">
                {/* YAML Editor Panel */}
                {showYamlPanel && (
                    <div className="w-80 flex flex-col glass rounded-2xl overflow-hidden">
                        <div className="px-4 py-3 border-b border-white/5">
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                                YAML Input
                            </p>
                        </div>
                        <textarea
                            value={yamlInput}
                            onChange={(e) => handleYamlChange(e.target.value)}
                            className="flex-1 bg-transparent text-slate-300 font-mono text-xs p-4 resize-none focus:outline-none"
                            placeholder="Paste your scenario YAML here..."
                            spellCheck={false}
                        />
                        {parseError && (
                            <div className="px-4 py-3 bg-rose-500/10 border-t border-rose-500/20">
                                <p className="text-xs font-mono text-rose-400">{parseError}</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Flow Canvas */}
                <div className="flex-1 glass rounded-2xl overflow-hidden relative">
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
                                    default: return '#64748b';
                                }
                            }}
                            maskColor="rgba(0,0,0,0.7)"
                        />
                    </ReactFlow>
                    <FlowLegend />
                </div>

                {/* Step Detail Panel */}
                <StepDetailPanel
                    step={selectedStep}
                    onClose={() => setSelectedStep(null)}
                />
            </div>
        </div>
    );
}

// ============================================================================
// Flow Generation
// ============================================================================

function generateFlowElements(scenario: Scenario): { nodes: Node[]; edges: Edge[] } {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    const nodeSpacingY = 100;
    const startY = 50;

    // Generate nodes for flow steps
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

        // Create edge to next node
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

    // Center nodes horizontally
    const maxWidth = 280;
    nodes.forEach((node) => {
        node.position.x = -maxWidth / 2;
    });

    return { nodes, edges };
}

export default ScenarioVisualizerPage;
