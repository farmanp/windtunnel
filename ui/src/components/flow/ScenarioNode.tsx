/**
 * ScenarioNode Component
 *
 * Custom React Flow node for scenario steps with action type styling.
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { ScenarioStep } from '@/lib/yamlParser';

export interface ScenarioNodeData extends Record<string, unknown> {
    step: ScenarioStep;
    label: string;
    description: string;
    index: number;
}

const actionConfig: Record<string, { bg: string; border: string; text: string; glow: string; icon: React.ReactNode }> = {
    http: {
        bg: 'bg-cyan-500/10',
        border: 'border-cyan-500/30',
        text: 'text-cyan-400',
        glow: 'shadow-[0_0_15px_rgba(6,182,212,0.2)]',
        icon: (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
        ),
    },
    wait: {
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/30',
        text: 'text-amber-400',
        glow: 'shadow-[0_0_15px_rgba(245,158,11,0.2)]',
        icon: (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
    },
    assert: {
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/30',
        text: 'text-emerald-400',
        glow: 'shadow-[0_0_15px_rgba(16,185,129,0.2)]',
        icon: (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
        ),
    },
};

interface ScenarioNodeProps {
    data: ScenarioNodeData;
    selected?: boolean;
}

function ScenarioNodeComponent({ data, selected }: ScenarioNodeProps) {
    const config = actionConfig[data.step.type] || actionConfig.http;

    return (
        <>
            <Handle
                type="target"
                position={Position.Top}
                className="!bg-slate-500 !border-slate-400 !w-2 !h-2"
            />

            <div
                className={`
                    min-w-[200px] max-w-[280px] px-4 py-3 rounded-xl
                    ${config.bg} ${config.border} border
                    backdrop-blur-sm transition-all duration-300
                    ${selected ? `${config.glow} ring-2 ring-white/20` : ''}
                    hover:scale-[1.02] cursor-pointer
                `}
            >
                {/* Header */}
                <div className="flex items-center gap-2 mb-2">
                    <span className={config.text}>{config.icon}</span>
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                        {data.step.type}
                    </span>
                    <span className="ml-auto text-[9px] font-mono text-slate-600">
                        #{data.index + 1}
                    </span>
                </div>

                {/* Name */}
                <p className="text-sm font-bold text-white mb-1 truncate">
                    {data.label}
                </p>

                {/* Description */}
                <p className="text-[11px] font-mono text-slate-400 truncate">
                    {data.description}
                </p>
            </div>

            <Handle
                type="source"
                position={Position.Bottom}
                className="!bg-slate-500 !border-slate-400 !w-2 !h-2"
            />
        </>
    );
}

export const ScenarioNode = memo(ScenarioNodeComponent);
