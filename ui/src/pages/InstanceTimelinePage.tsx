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
        body: any;
        errors: string[];
        turbulence?: Record<string, any>;
    };
}

interface InstanceDetail {
    instance_id: string;
    correlation_id: string;
    scenario_id: string;
    passed: boolean | null;
    duration_ms: number;
    entry: Record<string, any>;
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
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="w-12 h-12 border-2 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin"></div>
            </div>
        );
    }

    if (!instance) {
        return (
            <div className="text-center p-20 glass rounded-3xl">
                <p className="text-rose-400 font-black uppercase tracking-[0.2em] mb-2">TELEMETRY_GHOST</p>
                <p className="text-slate-500 text-sm">Target execution instance does not exist in the active artifact set.</p>
            </div>
        );
    }

    return (
        <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Breadcrumb */}
            <nav className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                <Link to="/" className="hover:text-cyan-400 transition-colors">Executions</Link>
                <span className="opacity-30">/</span>
                <Link to={`/runs/${runId}`} className="hover:text-cyan-400 transition-colors">{runId}</Link>
                <span className="opacity-30">/</span>
                <span className="text-slate-300">Instance {instanceId}</span>
            </nav>

            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <div className="flex items-center gap-4 mb-2">
                        <h1 className="text-4xl font-bold tracking-tight text-white glow-cyan">
                            Simulation Trace
                        </h1>
                        <StatusBadge status={instance.passed ? 'passed' : 'failed'} size="sm" />
                    </div>
                    <div className="flex items-center gap-4 text-xs font-bold uppercase tracking-widest text-slate-500">
                        <span className="text-slate-200">{instance.correlation_id}</span>
                        <span className="opacity-20">|</span>
                        <span className="text-cyan-500/80 italic">{instance.scenario_id}</span>
                        <span className="opacity-20">|</span>
                        <span className="text-slate-400">{instance.duration_ms.toFixed(1)}ms Lifetime</span>
                    </div>
                </div>
                <button className="flex items-center gap-2.5 px-6 py-3 rounded-xl glass glass-hover text-indigo-400 font-bold text-xs uppercase tracking-widest transition-all">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Re-reun Instance
                </button>
            </div>

            {/* Timeline Explorer */}
            <div className="relative space-y-6">
                {/* Cinematic Vertical Line */}
                <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-cyan-500/50 via-indigo-500/20 to-transparent shadow-[0_0_15px_rgba(6,182,212,0.2)]" />

                {/* Steps */}
                <div className="space-y-6">
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
    const typeIcons: Record<string, React.ReactNode> = {
        http: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
        ),
        wait: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
        assert: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
    };

    return (
        <div className="relative pl-14 animate-in slide-in-from-left-4 duration-500" style={{ animationDelay: `${step.index * 50}ms` }}>
            {/* Node Trace */}
            <div
                className={`absolute left-4 w-5 h-5 rounded-md border-2 rotate-45 flex items-center justify-center transition-all duration-500 z-10 ${step.observation.ok
                    ? 'border-emerald-500 bg-[#05070a] shadow-[0_0_10px_rgba(16,185,129,0.3)]'
                    : 'border-rose-500 bg-[#05070a] shadow-[0_0_10px_rgba(239,68,68,0.3)]'
                    }`}
            >
                <div className={`-rotate-45 text-[10px] font-black ${step.observation.ok ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {step.observation.ok ? '!' : '?'}
                </div>
            </div>

            {/* Step Artifact Card */}
            <div
                className={`glass rounded-2xl overflow-hidden transition-all duration-300 ${isExpanded ? 'ring-1 ring-white/10 shadow-2xl' : 'shadow-lg hover:shadow-cyan-900/10'}`}
            >
                {/* Toggle Panel */}
                <button
                    onClick={onToggle}
                    className="w-full flex items-center justify-between px-6 py-5 hover:bg-white/[0.02] transition-colors"
                >
                    <div className="flex items-center gap-5">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${step.observation.ok ? 'bg-emerald-500/5 text-emerald-400' : 'bg-rose-500/5 text-rose-400'}`}>
                            {typeIcons[step.type] || '•'}
                        </div>
                        <div className="text-left">
                            <p className="text-[10px] font-black uppercase tracking-[.2em] text-slate-500 mb-0.5">
                                Instruction {step.index + 1} • {step.type}
                            </p>
                            <p className="text-base font-bold text-slate-100 group-hover:text-white transition-colors">
                                {step.name}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-6">
                        <div className="text-right flex flex-col items-end">
                            <p className="text-xs font-mono font-bold text-slate-400 leading-none mb-1">
                                {step.observation.latency_ms.toFixed(1)}ms
                            </p>
                            {step.observation.turbulence && (
                                <span className="text-[10px] font-black text-amber-500 uppercase tracking-widest animate-pulse">
                                    Turbulence Active
                                </span>
                            )}
                        </div>
                        <svg
                            className={`w-5 h-5 text-slate-600 transition-transform duration-500 ${isExpanded ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>
                </button>

                {/* Detailed Investigation Content */}
                {isExpanded && (
                    <div className="px-8 pb-8 space-y-8 animate-in fade-in zoom-in-95 duration-300">
                        {/* Fail-State Diagnosis */}
                        {(!step.observation.ok || step.observation.errors.length > 0) && (
                            <div className="p-6 rounded-2xl bg-rose-500/5 border border-rose-500/10 relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-3 opacity-10">
                                    <svg className="w-12 h-12 text-rose-500" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                                    </svg>
                                </div>
                                <h3 className="text-[10px] font-black text-rose-500 uppercase tracking-[0.2em] mb-3">Signal Analysis Verdict</h3>
                                <div className="space-y-3">
                                    {step.observation.errors.length > 0 ? (
                                        step.observation.errors.map((error: string, i: number) => (
                                            <p key={i} className="text-sm text-rose-200 font-mono font-medium leading-relaxed bg-black/20 p-3 rounded-lg border border-white/5">
                                                {error}
                                            </p>
                                        ))
                                    ) : (
                                        <p className="text-sm text-rose-200 font-mono font-medium p-3 rounded-lg bg-black/20 border border-white/5">
                                            Sub-optimal terminal state detected (Status: {String(step.observation.status_code || 'N/A')})
                                        </p>
                                    )}
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-2 gap-8">
                            {/* Telemetry Matrix */}
                            <div className="space-y-6">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 rounded-xl glass border-white/5">
                                        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Status Code</p>
                                        <p className={`font-mono text-xl font-bold ${(step.observation.status_code ?? 0) < 400 ? 'text-emerald-400 glow-pass' : 'text-rose-400 glow-fail'}`}>
                                            {step.observation.status_code?.toString() || '---'}
                                        </p>
                                    </div>
                                    <div className="p-4 rounded-xl glass border-white/5">
                                        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Precision Latency</p>
                                        <p className="text-white font-mono text-xl font-bold">
                                            {step.observation.latency_ms.toFixed(3)}<span className="text-xs text-slate-500 ml-1">ms</span>
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Diagnostic Tools</p>
                                    <button
                                        onClick={() => {
                                            const url = new URL(window.location.href);
                                            url.hash = `step-${step.index}`;
                                            navigator.clipboard.writeText(url.toString());
                                        }}
                                        className="w-full flex items-center justify-between p-3 rounded-xl glass-hover border border-white/5 text-[10px] font-black uppercase tracking-widest text-cyan-400 transition-all"
                                    >
                                        Generate Direct Trace Link
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="m14.828 14.828a4 4 0 015.656 0l4-4a4 4 0 01-5.656-5.656l-1.102 1.101" />
                                        </svg>
                                    </button>
                                </div>
                            </div>

                            <div className="p-6 rounded-2xl bg-amber-500/[0.03] border border-amber-500/10">
                                <h3 className="text-[10px] font-black text-amber-500 uppercase tracking-[0.2em] mb-4">Turbulence Injection Matrix</h3>
                                <div className="space-y-4">
                                    {Object.entries(step.observation.turbulence || {}).map(([key, value]: [string, any]) => (
                                        <div key={key} className="flex items-center justify-between border-b border-white/5 pb-2">
                                            <span className="text-[10px] font-bold text-slate-500 uppercase">{key}</span>
                                            <span className="text-xs font-mono text-amber-400/80">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Signal Body Analysis */}
                        {step.observation.body && (
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Signal Artifact (JSON)</h3>
                                    <button
                                        onClick={() => navigator.clipboard.writeText(JSON.stringify(step.observation.body, null, 2))}
                                        className="text-[10px] font-black uppercase text-cyan-500/60 hover:text-cyan-400"
                                    >
                                        Copy Artifact
                                    </button>
                                </div>
                                <div className="rounded-2xl bg-black/40 border border-white/5 p-6 font-mono text-xs text-slate-400 overflow-x-auto selection:bg-cyan-500/30">
                                    <pre className="leading-relaxed">
                                        {JSON.stringify(step.observation.body, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
