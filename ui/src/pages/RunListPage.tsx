import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useMemo } from 'react';
import { StatusBadge } from '@/components/StatusBadge';
import { EmptyState } from '@/components/EmptyState';
import { SkeletonRow } from '@/components/Skeleton';
import { useMultiRunStream } from '@/hooks/useMultiRunStream';

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
    };
}

export function RunListPage() {
    const { data, isLoading, error, refetch } = useQuery<{ runs: Run[] }>({
        queryKey: ['runs'],
        queryFn: async () => {
            const res = await fetch('/api/runs');
            if (!res.ok) throw new Error('Failed to fetch runs');
            return res.json();
        },
        refetchInterval: 5000, // Auto-refresh for "engine alive" feel
    });

    // Get IDs of active runs for live streaming
    const activeRunIds = useMemo(() => {
        return data?.runs
            ?.filter(run => run.completed_at === null)
            ?.map(run => run.id) ?? [];
    }, [data?.runs]);

    // Subscribe to all active runs
    const { getStreamState } = useMultiRunStream(activeRunIds);

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            {/* Header */}
            <div className="flex items-end justify-between">
                <div>
                    <h1 className="text-4xl font-bold tracking-tight text-white glow-cyan mb-2">
                        Executions
                    </h1>
                    <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">
                        {data?.runs?.length ?? 0} Recorded Sessions
                        {activeRunIds.length > 0 && (
                            <span className="ml-3 text-cyan-400">
                                • {activeRunIds.length} Active
                            </span>
                        )}
                    </p>
                </div>
                <button
                    onClick={() => refetch()}
                    className="flex items-center gap-2.5 px-5 py-2.5 rounded-xl glass glass-hover text-cyan-400 font-bold text-xs uppercase tracking-widest transition-all"
                >
                    <svg className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Sync Engine
                </button>
            </div>

            {/* Table Container */}
            <div className="glass rounded-3xl overflow-hidden shadow-2xl">
                {/* Table Header */}
                <div className="grid grid-cols-6 gap-6 px-8 py-5 bg-white/[0.02] border-b border-white/5 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">
                    <div>Reference ID</div>
                    <div>Environment / SUT</div>
                    <div>Triggered</div>
                    <div>Compute Time</div>
                    <div className="text-center">Progress</div>
                    <div className="text-right">Integrity Status</div>
                </div>

                {/* Table Body */}
                <div className="divide-y divide-white/5">
                    {isLoading ? (
                        <div>
                            {[...Array(5)].map((_, i) => (
                                <SkeletonRow key={i} />
                            ))}
                        </div>
                    ) : error ? (
                        <div className="p-20 text-center">
                            <p className="text-rose-400 font-mono text-sm mb-2">ENGINE_IO_FAILURE</p>
                            <p className="text-slate-500 text-xs">Unable to establish connection with execution artifacts.</p>
                        </div>
                    ) : data?.runs?.length === 0 ? (
                        <EmptyState
                            title="No Valid Executions"
                            description="Deploy a scenario to the engine to begin stress processing."
                            icon={
                                <svg className="w-12 h-12 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                            }
                        />
                    ) : (
                        data?.runs?.map((run) => (
                            <RunRow key={run.id} run={run} streamState={getStreamState(run.id)} />
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}

interface RunRowProps {
    run: Run;
    streamState?: {
        status: 'connecting' | 'connected' | 'disconnected';
        liveStats: {
            completed: number;
            passed: number;
            failed: number;
            errors: number;
            passRate: number;
        };
    };
}

function RunRow({ run, streamState }: RunRowProps) {
    const isRunning = run.completed_at === null;

    // Use live stats if available for running runs
    const displayStats = isRunning && streamState?.liveStats.completed
        ? streamState.liveStats
        : {
            passed: run.stats.passed,
            failed: run.stats.failed,
            errors: run.stats.errors,
            completed: run.stats.passed + run.stats.failed,
            passRate: run.stats.pass_rate,
        };

    const progressPercentage = run.stats.total > 0
        ? Math.round((displayStats.completed / run.stats.total) * 100)
        : 0;

    // Determine status
    const status = isRunning ? 'running' : (run.stats.failed > 0 || run.stats.errors > 0) ? 'failed' : 'passed';

    // Connection indicator
    const isConnected = streamState?.status === 'connected';

    return (
        <Link
            to={`/runs/${run.id}`}
            className="grid grid-cols-6 gap-6 px-8 py-6 glass-hover transition-all duration-300 group items-center"
        >
            <div className="font-mono text-sm font-bold text-white group-hover:text-cyan-400 transition-colors flex items-center gap-2">
                {run.id}
                {/* Live indicator for active runs */}
                {isRunning && isConnected && (
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_6px_rgba(6,182,212,0.5)]" />
                )}
            </div>
            <div>
                <p className="text-sm font-semibold text-slate-200">{run.sut_name}</p>
                <p className="text-[10px] font-medium text-slate-500 truncate">{run.scenarios.join(' • ')}</p>
            </div>
            <div className="text-xs font-medium text-slate-400">
                {formatRelativeTime(run.started_at)}
            </div>
            <div className="font-mono text-xs text-slate-400">
                {formatDuration(run.stats.duration_ms)}
            </div>
            <div className="flex flex-col items-center gap-2">
                {/* Progress Bar */}
                <div className="w-24 h-1.5 rounded-full bg-white/5 overflow-hidden relative">
                    {isRunning && streamState?.status === 'connecting' ? (
                        // Indeterminate shimmer for connecting state
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent animate-shimmer" />
                    ) : (
                        // Segmented progress
                        <div className="flex h-full">
                            {/* Passed segment */}
                            <div
                                className="h-full bg-emerald-500 transition-all duration-500"
                                style={{ width: `${run.stats.total > 0 ? (displayStats.passed / run.stats.total) * 100 : 0}%` }}
                            />
                            {/* Failed segment */}
                            <div
                                className="h-full bg-rose-500 transition-all duration-500"
                                style={{ width: `${run.stats.total > 0 ? (displayStats.failed / run.stats.total) * 100 : 0}%` }}
                            />
                        </div>
                    )}
                </div>

                {/* Stats label */}
                <div className="flex items-center gap-1.5">
                    {isRunning ? (
                        // Show progress for running
                        <>
                            <span className="text-[10px] font-black text-cyan-400 tabular-nums">
                                {progressPercentage}%
                            </span>
                            <span className="text-[9px] text-slate-500">
                                ({displayStats.completed}/{run.stats.total})
                            </span>
                        </>
                    ) : (
                        // Show pass rate for completed
                        <span className={`text-[10px] font-black tracking-widest ${displayStats.passRate >= 95 ? 'text-emerald-400' :
                                displayStats.passRate >= 80 ? 'text-amber-400' :
                                    'text-rose-400'
                            }`}>
                            {displayStats.passRate.toFixed(1)}%
                        </span>
                    )}
                </div>
            </div>
            <div className="flex justify-end">
                <StatusBadge status={status} size="sm" />
            </div>
        </Link>
    );
}

function formatRelativeTime(isoString: string): string {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hr ago`;
    return `${diffDays} days ago`;
}

function formatDuration(ms: number): string {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    const seconds = ms / 1000;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
}
