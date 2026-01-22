/**
 * StepDetailPanel Component
 *
 * Right-side panel showing selected step configuration details.
 */

import { useMemo } from 'react';
import type { ScenarioStep } from '@/lib/yamlParser';

interface StepDetailPanelProps {
    step: ScenarioStep | null;
    onClose: () => void;
}

export function StepDetailPanel({ step, onClose }: StepDetailPanelProps) {
    const jsonContent = useMemo(() => {
        if (!step) return '';
        return JSON.stringify(step, null, 2);
    }, [step]);

    // Highlight template variables in JSON
    const highlightedJson = useMemo(() => {
        return jsonContent.replace(
            /\{\{([^}]+)\}\}/g,
            '<span class="text-cyan-400 font-bold">{{$1}}</span>'
        );
    }, [jsonContent]);

    if (!step) {
        return (
            <div className="w-80 glass rounded-2xl p-6 flex flex-col items-center justify-center text-center h-full">
                <svg className="w-12 h-12 text-slate-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                </svg>
                <p className="text-sm font-medium text-slate-500">
                    Click a step to view details
                </p>
            </div>
        );
    }

    const typeColors = {
        http: 'text-cyan-400 border-cyan-500/30',
        wait: 'text-amber-400 border-amber-500/30',
        assert: 'text-emerald-400 border-emerald-500/30',
        branch: 'text-purple-400 border-purple-500/30',
    };

    return (
        <div className="w-80 glass rounded-2xl overflow-hidden flex flex-col h-full">
            {/* Header */}
            <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className={`text-xs font-black uppercase tracking-widest ${typeColors[step.type]}`}>
                        {step.type}
                    </span>
                    <span className="text-slate-500">•</span>
                    <span className="text-sm font-bold text-white truncate max-w-[150px]">
                        {step.name}
                    </span>
                </div>
                <button
                    onClick={onClose}
                    className="p-1 rounded-md hover:bg-white/10 transition-colors text-slate-500 hover:text-white"
                >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-4">
                <div className="space-y-4">
                    {/* Type-specific summary */}
                    {step.type === 'http' && (
                        <div className="space-y-2">
                            <DetailRow label="Method" value={step.method || 'GET'} />
                            <DetailRow label="Path" value={step.path || '/'} mono />
                            {step.service && <DetailRow label="Service" value={step.service} />}
                        </div>
                    )}

                    {step.type === 'wait' && (
                        <div className="space-y-2">
                            <DetailRow label="Path" value={step.path || '/'} mono />
                            <DetailRow label="Timeout" value={`${step.timeout_seconds || 30}s`} />
                            <DetailRow label="Interval" value={`${step.interval_seconds || 1}s`} />
                        </div>
                    )}

                    {step.type === 'assert' && step.expect && (
                        <div className="space-y-2">
                            {step.expect.status_code && (
                                <DetailRow label="Status" value={String(step.expect.status_code)} />
                            )}
                            {step.expect.jsonpath && (
                                <DetailRow label="JSONPath" value={step.expect.jsonpath} mono />
                            )}
                            {step.expect.equals && (
                                <DetailRow label="Equals" value={step.expect.equals} mono />
                            )}
                        </div>
                    )}

                    {/* Extractions */}
                    {step.type === 'http' && step.extract && Object.keys(step.extract).length > 0 && (
                        <div className="pt-3 border-t border-white/5">
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">
                                Extractions
                            </p>
                            <div className="space-y-1.5">
                                {Object.entries(step.extract).map(([key, path]) => (
                                    <div key={key} className="flex items-start gap-2 text-xs">
                                        <span className="text-cyan-400 font-mono">{key}</span>
                                        <span className="text-slate-600">←</span>
                                        <span className="text-slate-400 font-mono flex-1 break-all">{path}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Full JSON */}
                    <div className="pt-3 border-t border-white/5">
                        <div className="flex items-center justify-between mb-2">
                            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                                Full Configuration
                            </p>
                            <button
                                onClick={() => navigator.clipboard.writeText(jsonContent)}
                                className="text-[10px] font-bold text-slate-500 hover:text-cyan-400 transition-colors"
                            >
                                Copy
                            </button>
                        </div>
                        <pre
                            className="text-[11px] font-mono text-slate-400 bg-black/20 rounded-lg p-3 overflow-x-auto"
                            dangerouslySetInnerHTML={{ __html: highlightedJson }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

function DetailRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
    return (
        <div className="flex items-start gap-3">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 w-16 flex-shrink-0">
                {label}
            </span>
            <span className={`text-xs text-slate-300 break-all ${mono ? 'font-mono' : ''}`}>
                {value}
            </span>
        </div>
    );
}
