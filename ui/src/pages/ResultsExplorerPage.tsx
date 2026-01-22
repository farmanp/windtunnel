/**
 * ResultsExplorerPage
 * 
 * Advanced search, filtering, and comparison of run results.
 */

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { StatusBadge } from '@/components/StatusBadge';
import { SkeletonRow } from '@/components/Skeleton';

interface Run {
    id: string;
    sut_name: string;
    scenarios: string[];
    started_at: string;
    completed_at: string | null;
    stats: {
        total: number;
        passed: number;
        failed: number;
        errors: number;
        pass_rate: number;
        duration_ms: number;
        p95_latency_ms: number;
    };
}

type StatusFilter = 'all' | 'passed' | 'failed' | 'slow';

export function ResultsExplorerPage() {
    // Filter state
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
    const [slowThreshold, setSlowThreshold] = useState(500);
    const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set());
    const [showComparison, setShowComparison] = useState(false);

    // Fetch runs with filters
    const { data, isLoading } = useQuery<{ runs: Run[] }>({
        queryKey: ['explorer', 'runs', searchQuery, statusFilter, slowThreshold],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (searchQuery) params.append('query', searchQuery);
            
            // Map 'slow' filter to backend param
            if (statusFilter === 'slow') {
                params.append('slow_threshold', slowThreshold.toString());
            } else if (statusFilter !== 'all') {
                params.append('status', statusFilter);
            }
            
            const res = await fetch(`/api/runs?${params.toString()}`);
            if (!res.ok) throw new Error('Failed to fetch filtered runs');
            return res.json();
        }
    });

    const runs = data?.runs ?? [];

    // Comparison logic
    const handleSelectRun = (runId: string) => {
        const next = new Set(selectedRuns);
        if (next.has(runId)) {
            next.delete(runId);
        } else if (next.size < 2) {
            next.add(runId);
        }
        setSelectedRuns(next);
    };

    const comparisonData = useMemo(() => {
        if (selectedRuns.size !== 2) return null;
        const ids = Array.from(selectedRuns);
        return [
            runs.find(r => r.id === ids[0]),
            runs.find(r => r.id === ids[1])
        ].filter(Boolean) as Run[];
    }, [selectedRuns, runs]);

    // Export utilities
    const exportToJSON = () => {
        const blob = new Blob([JSON.stringify(runs, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `turbulence-export-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
    };

    const exportToCSV = () => {
        const headers = ['Run ID', 'SUT', 'Scenarios', 'Started At', 'Status', 'Total', 'Passed', 'Failed', 'Pass Rate %', 'p95 Latency (ms)'];
        const rows = runs.map(r => [
            r.id,
            r.sut_name,
            r.scenarios.join('; '),
            r.started_at,
            r.completed_at ? 'Completed' : 'Running',
            r.stats.total,
            r.stats.passed,
            r.stats.failed,
            r.stats.pass_rate.toFixed(1),
            r.stats.p95_latency_ms.toFixed(1)
        ]);
        
        const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n");
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `turbulence-export-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            {/* Header */}
            <div className="flex items-end justify-between">
                <div>
                    <h1 className="text-4xl font-bold tracking-tight text-white glow-cyan mb-2">
                        Results Explorer
                    </h1>
                    <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">
                        Advanced Filtering & Comparison
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={exportToJSON}
                        className="px-4 py-2 rounded-xl glass glass-hover text-slate-400 text-[10px] font-black uppercase tracking-widest transition-all"
                    >
                        Export JSON
                    </button>
                    <button
                        onClick={exportToCSV}
                        className="px-4 py-2 rounded-xl glass glass-hover text-cyan-400 text-[10px] font-black uppercase tracking-widest transition-all"
                    >
                        Export CSV
                    </button>
                </div>
            </div>

            {/* Filter Bar */}
            <div className="glass rounded-3xl p-6 flex flex-wrap items-center gap-6 shadow-xl border-white/5">
                {/* Search */}
                <div className="flex-1 min-w-[300px] relative group">
                    <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                        <svg className="w-4 h-4 text-slate-500 group-focus-within:text-cyan-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search by Run ID, SUT, or Scenario..."
                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-3 pl-12 pr-4 text-sm text-slate-200 focus:outline-none focus:ring-2 ring-cyan-500/50 transition-all"
                    />
                </div>

                {/* Status Filter */}
                <div className="flex gap-1.5 p-1 rounded-xl bg-white/5 border border-white/5">
                    {(['all', 'passed', 'failed', 'slow'] as StatusFilter[]).map((f) => (
                        <button
                            key={f}
                            onClick={() => setStatusFilter(f)}
                            className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-300 ${statusFilter === f
                                ? 'bg-cyan-500 text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]'
                                : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                                }`}
                        >
                            {f}
                        </button>
                    ))}
                </div>

                {/* Slow Threshold */}
                {statusFilter === 'slow' && (
                    <div className="flex items-center gap-3 animate-in slide-in-from-left-2 duration-300">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Threshold</label>
                        <div className="flex items-center gap-2 bg-white/5 border border-white/5 rounded-lg px-3 py-1">
                            <input
                                type="number"
                                value={slowThreshold}
                                onChange={(e) => setSlowThreshold(parseInt(e.target.value))}
                                className="w-16 bg-transparent text-sm font-bold text-cyan-400 focus:outline-none"
                            />
                            <span className="text-[10px] font-bold text-slate-600 uppercase">ms</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Selection Toolbar */}
            {selectedRuns.size > 0 && (
                <div className="flex items-center justify-between px-8 py-4 bg-cyan-500 rounded-2xl shadow-[0_0_30px_rgba(6,182,212,0.2)] animate-in slide-in-from-top-4 duration-500">
                    <div className="flex items-center gap-4">
                        <span className="text-black font-black uppercase tracking-widest text-xs">
                            {selectedRuns.size} Run{selectedRuns.size > 1 ? 's' : ''} Selected
                        </span>
                        <div className="flex gap-2">
                            {Array.from(selectedRuns).map(id => (
                                <span key={id} className="bg-black/20 text-black font-mono text-[10px] px-2 py-0.5 rounded border border-black/10">
                                    {id}
                                </span>
                            ))}
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button 
                            onClick={() => setSelectedRuns(new Set())}
                            className="text-black/60 hover:text-black font-bold text-[10px] uppercase tracking-widest transition-colors"
                        >
                            Clear
                        </button>
                        <button
                            disabled={selectedRuns.size !== 2}
                            onClick={() => setShowComparison(true)}
                            className={`px-6 py-2 rounded-xl font-black uppercase tracking-widest text-[10px] transition-all ${selectedRuns.size === 2 
                                ? 'bg-black text-cyan-400 hover:scale-[1.05]' 
                                : 'bg-black/10 text-black/40 cursor-not-allowed'
                            }`}
                        >
                            Compare Side-by-Side
                        </button>
                    </div>
                </div>
            )}

            {/* Results Grid */}
            <div className="glass rounded-3xl overflow-hidden shadow-2xl">
                <div className="grid grid-cols-12 gap-6 px-8 py-5 bg-white/[0.02] border-b border-white/5 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                    <div className="col-span-1"></div>
                    <div className="col-span-2">Reference ID</div>
                    <div className="col-span-3">Environment / SUT</div>
                    <div className="col-span-2 text-right">Pass Rate</div>
                    <div className="col-span-2 text-right">p95 Latency</div>
                    <div className="col-span-2 text-right">Status</div>
                </div>

                <div className="divide-y divide-white/5">
                    {isLoading ? (
                        <div>{[...Array(5)].map((_, i) => <SkeletonRow key={i} />)}</div>
                    ) : runs.length === 0 ? (
                        <div className="p-20 text-center text-slate-500 text-xs italic">
                            No telemetry data matches the current filter matrix.
                        </div>
                    ) : (
                        runs.map((run) => (
                            <div 
                                key={run.id} 
                                onClick={() => handleSelectRun(run.id)}
                                className={`grid grid-cols-12 gap-6 px-8 py-6 items-center transition-all cursor-pointer group ${selectedRuns.has(run.id) ? 'bg-cyan-500/10' : 'hover:bg-white/[0.03]'}`}
                            >
                                <div className="col-span-1">
                                    <div className={`w-5 h-5 rounded border-2 transition-all flex items-center justify-center ${selectedRuns.has(run.id) 
                                        ? 'bg-cyan-500 border-cyan-500' 
                                        : 'border-white/10 group-hover:border-white/20'}`}>
                                        {selectedRuns.has(run.id) && (
                                            <svg className="w-3 h-3 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={4}>
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                            </svg>
                                        )}
                                    </div>
                                </div>
                                <div className="col-span-2 font-mono text-sm font-bold text-slate-300 group-hover:text-white transition-colors">
                                    {run.id}
                                </div>
                                <div className="col-span-3">
                                    <p className="text-sm font-bold text-slate-200">{run.sut_name}</p>
                                    <p className="text-[10px] font-medium text-slate-500 truncate">{run.scenarios.join(' • ')}</p>
                                </div>
                                <div className={`col-span-2 text-right font-black text-sm tabular-nums ${run.stats.pass_rate >= 95 ? 'text-emerald-400' : run.stats.pass_rate >= 80 ? 'text-amber-400' : 'text-rose-400'}`}>
                                    {run.stats.pass_rate.toFixed(1)}%
                                </div>
                                <div className={`col-span-2 text-right font-mono text-sm tabular-nums ${run.stats.p95_latency_ms > slowThreshold ? 'text-amber-400' : 'text-slate-400'}`}>
                                    {run.stats.p95_latency_ms.toFixed(1)}ms
                                </div>
                                <div className="col-span-2 flex justify-end">
                                    <StatusBadge status={run.completed_at ? (run.stats.failed > 0 ? 'failed' : 'passed') : 'running'} size="sm" />
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Comparison Modal */}
            {showComparison && comparisonData && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-12 backdrop-blur-xl bg-black/60 animate-in fade-in duration-300">
                    <div className="bg-[#0a0f18] border border-white/10 rounded-[2.5rem] w-full max-w-6xl max-h-full flex flex-col shadow-[0_0_100px_rgba(0,0,0,0.5)] overflow-hidden">
                        {/* Modal Header */}
                        <div className="px-10 py-8 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                            <div>
                                <h2 className="text-2xl font-bold text-white mb-1">Execution Comparison</h2>
                                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-500/60">Metric Matrix Alignment</p>
                            </div>
                            <button 
                                onClick={() => setShowComparison(false)}
                                className="w-10 h-10 rounded-full glass glass-hover flex items-center justify-center text-slate-500 hover:text-white transition-all"
                            >
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        {/* Modal Content */}
                        <div className="flex-1 overflow-auto p-10">
                            <div className="grid grid-cols-2 gap-12">
                                {comparisonData.map((run, idx) => (
                                    <div key={run.id} className="space-y-8 animate-in slide-in-from-bottom-4 duration-700" style={{ animationDelay: `${idx * 150}ms` }}>
                                        {/* Run Header */}
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-3">
                                                <span className={`w-3 h-3 rounded-full ${idx === 0 ? 'bg-cyan-500' : 'bg-indigo-500'}`} />
                                                <h3 className="text-xl font-bold text-white font-mono">{run.id}</h3>
                                            </div>
                                            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">{run.sut_name}</p>
                                        </div>

                                        {/* Metric Grid */}
                                        <div className="grid grid-cols-2 gap-4">
                                            <MetricComparison label="Success Rate" value={`${run.stats.pass_rate.toFixed(1)}%`} sub="Per agent overhead" />
                                            <MetricComparison label="p95 Latency" value={`${run.stats.p95_latency_ms.toFixed(1)}ms`} sub="Tail performance" />
                                            <MetricComparison label="Error Volume" value={run.stats.errors} sub="System exceptions" />
                                            <MetricComparison label="Avg Duration" value={`${(run.stats.duration_ms / run.stats.total).toFixed(1)}ms`} sub="Per agent overhead" />
                                        </div>

                                        {/* Failures */}
                                        <div className="space-y-4 pt-4 border-t border-white/5">
                                            <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-600">Top Failure Signatures</h4>
                                            <div className="space-y-2">
                                                {run.stats.failed === 0 ? (
                                                    <p className="text-sm text-emerald-500/60 font-medium italic">Zero regressions detected.</p>
                                                ) : (
                                                    <div className="space-y-2">
                                                        {/* We don't have detailed failures in the list API, 
                                                            normally we'd fetch them or pass them. 
                                                            For now just summary. */}
                                                        <p className="text-sm text-rose-400 font-bold">{run.stats.failed} total instances failed</p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function MetricComparison({ label, value, sub }: { label: string; value: string | number; sub: string }) {
    return (
        <div className="bg-white/[0.03] border border-white/5 rounded-2xl p-5 space-y-1">
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">{label}</p>
            <p className="text-2xl font-bold text-white tracking-tight tabular-nums">{value}</p>
            <p className="text-[10px] font-medium text-slate-600 truncate">{sub}</p>
        </div>
    );
}
