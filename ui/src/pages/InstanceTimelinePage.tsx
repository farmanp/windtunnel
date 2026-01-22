import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { useState } from 'react';
import { StatusBadge } from '@/components/StatusBadge';

interface Step {
    index: number;
    name: string;
    type: string;
    observation: {
        ok: boolean;
        status_code: number | null;
        latency_ms: number;
        headers: Record<string, string>;
        body: unknown;
        errors: string[];
        turbulence?: Record<string, unknown>;
    };
}

interface InstanceDetail {
    instance_id: string;
    correlation_id: string;
    scenario_id: string;
    passed: boolean | null;
    duration_ms: number;
    entry: Record<string, unknown>;
    steps: Step[];
}

export function InstanceTimelinePage() {
    const { runId, instanceId } = useParams<{ runId: string; instanceId: string }>();
    const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

    const { data: instance, isLoading } = useQuery<InstanceDetail>({
        queryKey: ['runs', runId, 'instances', instanceId],
        queryFn: async () => {
            const res = await fetch(`/api/runs/${runId}/instances/${instanceId}`);
            if (!res.ok) throw new Error('Failed to fetch instance');
            return res.json();
        },
    });

    const toggleStep = (index: number) => {
        setExpandedSteps(prev => {
            const next = new Set(prev);
            if (next.has(index)) {
                next.delete(index);
            } else {
                next.add(index);
            }
            return next;
        });
    };

    if (isLoading) {
        return <div className="text-[hsl(var(--color-text-secondary))]">Loading...</div>;
    }

    if (!instance) {
        return <div className="text-red-400">Instance not found</div>;
    }

    return (
        <div>
            {/* Breadcrumb */}
            <nav className="text-sm text-[hsl(var(--color-text-secondary))] mb-4">
                <Link to="/" className="hover:text-[hsl(var(--color-text-primary))]">Runs</Link>
                <span className="mx-2">›</span>
                <Link to={`/runs/${runId}`} className="hover:text-[hsl(var(--color-text-primary))]">{runId}</Link>
                <span className="mx-2">›</span>
                <span className="text-[hsl(var(--color-text-primary))]">{instanceId}</span>
            </nav>

            {/* Header */}
            <div className="flex items-start justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-semibold text-[hsl(var(--color-text-primary))]">
                        Instance {instanceId}
                    </h1>
                    <div className="flex items-center gap-4 mt-2 text-sm text-[hsl(var(--color-text-secondary))]">
                        <span className="font-mono">{instance.correlation_id}</span>
                        <span>•</span>
                        <span>{instance.scenario_id}</span>
                        <span>•</span>
                        <StatusBadge status={instance.passed ? 'passed' : 'failed'} size="sm" />
                    </div>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[hsl(var(--color-info))] hover:opacity-90 text-white font-medium transition-opacity">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Replay
                </button>
            </div>

            {/* Timeline */}
            <div className="relative">
                {/* Vertical line */}
                <div className="absolute left-4 top-0 bottom-0 w-px bg-[hsl(var(--color-border))]" />

                {/* Steps */}
                <div className="space-y-4">
                    {instance.steps.map((step) => (
                        <StepCard
                            key={step.index}
                            step={step}
                            isExpanded={expandedSteps.has(step.index)}
                            onToggle={() => toggleStep(step.index)}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}

interface StepCardProps {
    step: Step;
    isExpanded: boolean;
    onToggle: () => void;
}

function StepCard({ step, isExpanded, onToggle }: StepCardProps) {
    const typeIcons: Record<string, string> = {
        http: '🌐',
        wait: '⏳',
        assert: '✓',
    };

    return (
        <div className="relative pl-10">
            {/* Node */}
            <div
                className={`absolute left-2 w-5 h-5 rounded-full border-2 flex items-center justify-center text-xs ${step.observation.ok
                        ? 'border-green-500 bg-green-500/20 text-green-400'
                        : 'border-red-500 bg-red-500/20 text-red-400'
                    }`}
            >
                {step.observation.ok ? '✓' : '✗'}
            </div>

            {/* Card */}
            <div
                className={`bg-[hsl(var(--color-bg-secondary))] rounded-xl border transition-colors ${step.observation.ok
                        ? 'border-[hsl(var(--color-border))]'
                        : 'border-red-500/50'
                    }`}
            >
                {/* Summary */}
                <button
                    onClick={onToggle}
                    className="w-full flex items-center justify-between p-4 hover:bg-[hsl(var(--color-bg-elevated))] rounded-t-xl transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <span className="text-lg">{typeIcons[step.type] || '●'}</span>
                        <div className="text-left">
                            <p className="font-medium text-[hsl(var(--color-text-primary))]">
                                Step {step.index + 1}: {step.name}
                            </p>
                            <p className="text-sm text-[hsl(var(--color-text-secondary))]">
                                [{step.type.toUpperCase()}] {step.observation.latency_ms.toFixed(0)}ms
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        {step.observation.turbulence && (
                            <span className="px-2 py-1 rounded text-xs bg-amber-500/20 text-amber-400">
                                ⚠️ Turbulence
                            </span>
                        )}
                        <svg
                            className={`w-5 h-5 text-[hsl(var(--color-text-secondary))] transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>
                </button>

                {/* Expanded Detail */}
                {isExpanded && (
                    <div className="border-t border-[hsl(var(--color-border))] p-4 space-y-4">
                        {/* Status Code */}
                        {step.observation.status_code !== null && (
                            <div>
                                <p className="text-xs text-[hsl(var(--color-text-secondary))] mb-1">Status Code</p>
                                <p className={`font-mono ${step.observation.status_code < 400 ? 'text-green-400' : 'text-red-400'
                                    }`}>
                                    {step.observation.status_code}
                                </p>
                            </div>
                        )}

                        {/* Errors */}
                        {step.observation.errors.length > 0 && (
                            <div>
                                <p className="text-xs text-[hsl(var(--color-text-secondary))] mb-1">Errors</p>
                                <div className="space-y-1">
                                    {step.observation.errors.map((error, i) => (
                                        <p key={i} className="text-sm text-red-400 font-mono">{error}</p>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Response Body */}
                        {step.observation.body && (
                            <div>
                                <p className="text-xs text-[hsl(var(--color-text-secondary))] mb-1">Response Body</p>
                                <pre className="p-3 rounded-lg bg-[hsl(var(--color-bg-primary))] text-sm font-mono text-[hsl(var(--color-text-primary))] overflow-x-auto">
                                    {JSON.stringify(step.observation.body, null, 2)}
                                </pre>
                            </div>
                        )}

                        {/* Turbulence */}
                        {step.observation.turbulence && (
                            <div>
                                <p className="text-xs text-[hsl(var(--color-text-secondary))] mb-1">Turbulence Details</p>
                                <pre className="p-3 rounded-lg bg-amber-500/10 text-sm font-mono text-amber-400 overflow-x-auto">
                                    {JSON.stringify(step.observation.turbulence, null, 2)}
                                </pre>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
