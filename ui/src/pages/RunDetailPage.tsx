import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { useState, useMemo } from 'react';
import { StatusBadge } from '@/components/StatusBadge';
import { MetricCard } from '@/components/MetricCard';
import { SkeletonRow, SkeletonCard } from '@/components/Skeleton';
import { ProgressBar } from '@/components/ProgressBar';
import { FailureLink } from '@/components/FailureLink';
import { useRunStream } from '@/hooks/useRunStream';

type FilterType = 'all' | 'passed' | 'failed' | 'errors';

interface Instance {
    instance_id: string;
    correlation_id: string;
    scenario_id: string;
    passed: boolean | null;
    duration_ms: number;
    error: string | null;
}

interface Failure {
    message: string;
    count: number;
    percentage: number;
}

interface RunDetail {
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
    failures: Failure[];
}

export function RunDetailPage() {
    const { runId } = useParams<{ runId: string }>();
    const [filter, setFilter] = useState<FilterType>('all');
    const [showAllFailures, setShowAllFailures] = useState(false);

    // Real-time streaming with live stats
    const {
        status: streamStatus,
        liveStats,
        failures: liveFailures,
        isComplete,
        reconnect
    } = useRunStream(runId || '');

    const { data: run, isLoading: runLoading } = useQuery<RunDetail>({
        queryKey: ['runs', runId],
        queryFn: async () => {
            const res = await fetch(`/api/runs/${runId}`);
            if (!res.ok) throw new Error('Failed to fetch run');
            return res.json();
        },
    });

    const { data: instancesData, isLoading: instancesLoading } = useQuery<{ instances: Instance[] }>({
        queryKey: ['runs', runId, 'instances', filter],
        queryFn: async () => {
            const params = filter !== 'all' ? `?status=${filter}` : '';
            const res = await fetch(`/api/runs/${runId}/instances${params}`);
            if (!res.ok) throw new Error('Failed to fetch instances');
            return res.json();
        },
    });

    // Determine if this is an active run
    const isRunning = run?.completed_at === null;

    // Use live stats if running, otherwise use fetched stats
    const displayStats = useMemo(() => {
        if (isRunning && liveStats.completed > 0) {
            return {
                total: run?.stats.total ?? 0,
                passed: liveStats.passed,
                failed: liveStats.failed,
                errors: liveStats.errors,
                completed: liveStats.completed,
                passRate: liveStats.passRate,
            };
        }
        return {
            total: run?.stats.total ?? 0,
            passed: run?.stats.passed ?? 0,
            failed: run?.stats.failed ?? 0,
            errors: run?.stats.errors ?? 0,
            completed: (run?.stats.passed ?? 0) + (run?.stats.failed ?? 0),
            passRate: run?.stats.pass_rate ?? 0,
        };
    }, [isRunning, liveStats, run]);

    // Limit displayed live failures
    const displayedFailures = showAllFailures
        ? liveFailures
        : liveFailures.slice(0, 5);

    const passRateVariant =
        displayStats.passRate >= 95 ? 'success' :
            displayStats.passRate >= 80 ? 'warning' :
                'failure';

    return (
        <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Breadcrumb */}
            <nav className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                <Link to="/" className="hover:text-cyan-400 transition-colors">Executions</Link>
                <span className="opacity-30">/</span>
                <span className="text-slate-300">{runId}</span>
            </nav>

            {/* Header with Live Progress */}
            <div className="space-y-6">
                <div className="flex items-center gap-4">
                    <h1 className="text-4xl font-bold tracking-tight text-white glow-cyan">
                        {runId}
                    </h1>
                    {/* Connection Status Indicator */}
                    <button
                        onClick={streamStatus === 'disconnected' ? reconnect : undefined}
                        className={`px-3 py-1 rounded-md glass text-[10px] font-black uppercase tracking-widest flex items-center gap-2 transition-all ${streamStatus === 'connected'
                            ? 'border-emerald-500/20 text-emerald-400'
                            : streamStatus === 'connecting'
                                ? 'border-amber-500/20 text-amber-400'
                                : 'border-rose-500/20 text-rose-400 hover:border-rose-500/40 cursor-pointer'
                            }`}
                    >
                        <span className={`w-1.5 h-1.5 rounded-full ${streamStatus === 'connected'
                            ? 'bg-emerald-500 shadow-[0_0_6px_#10b981]'
                            : streamStatus === 'connecting'
                                ? 'bg-amber-500 animate-pulse'
                                : 'bg-rose-500'
                            }`} />
                        {streamStatus === 'connected' ? 'Live Stream' : streamStatus === 'connecting' ? 'Connecting...' : 'Reconnect'}
                    </button>

                    {/* Run completion indicator */}
                    {isComplete && (
                        <span className="px-3 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                            Completed
                        </span>
                    )}
                </div>

                {run && (
                    <p className="text-sm font-medium text-slate-400">
                        <span className="text-slate-600 uppercase text-[10px] font-black tracking-widest mr-2">System Under Test</span>
                        <span className="text-slate-200">{run.sut_name}</span>
                        <span className="mx-3 opacity-20">|</span>
                        <span className="text-slate-400 italic">{run.scenarios.join(' • ')}</span>
                    </p>
                )}

                {/* Live Progress Bar - Only show for active runs */}
                {isRunning && (
                    <div className="glass rounded-2xl p-6">
                        <ProgressBar
                            total={displayStats.total}
                            completed={displayStats.completed}
                            passed={displayStats.passed}
                            failed={displayStats.failed}
                            isConnecting={streamStatus === 'connecting'}
                            showCounts={true}
                            size="md"
                        />
                    </div>
                )}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-12 gap-6">
                {/* Left: Metric Cards (3 cols each, taking 9 cols total when no live failures) */}
                <div className={`${liveFailures.length > 0 && isRunning ? 'col-span-9' : 'col-span-12'}`}>
                    <div className="grid grid-cols-4 gap-6">
                        {runLoading ? (
                            <>
                                <SkeletonCard />
                                <SkeletonCard />
                                <SkeletonCard />
                                <SkeletonCard />
                            </>
                        ) : run && (
                            <>
                                <MetricCard
                                    label="Success Delta"
                                    value={`${displayStats.passRate.toFixed(1)}%`}
                                    variant={passRateVariant}
                                    sublabel="Workflow completion integrity"
                                    tooltip="Percentage of instances that reached terminal success. 100% indicates zero regression."
                                />
                                <MetricCard
                                    label="Compute Time"
                                    value={formatDuration(run.stats.duration_ms)}
                                    sublabel="Total execution duration"
                                    tooltip="The cumulative time spent by all virtual agents in this execution graph."
                                />
                                <MetricCard
                                    label="Population"
                                    value={displayStats.total}
                                    sublabel={`${displayStats.passed} Passed • ${displayStats.failed} Failed`}
                                    tooltip="The total number of concurrent instances spawned for this session."
                                />
                                <MetricCard
                                    label="IO Errors"
                                    value={displayStats.errors}
                                    variant={displayStats.errors > 0 ? 'warning' : 'default'}
                                    sublabel="Network / Host exceptions"
                                    tooltip="Non-assertion failures. These represent infra stability issues rather than logic bugs."
                                />
                            </>
                        )}
                    </div>
                </div>

                {/* Right: Live Failures Sidebar - Only show for active runs with failures */}
                {liveFailures.length > 0 && isRunning && (
                    <div className="col-span-3 space-y-3">
                        <div className="flex items-center justify-between">
                            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-rose-400 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                                Live Failures
                            </h3>
                            <span className="text-[10px] font-bold text-slate-500">
                                {liveFailures.length} total
                            </span>
                        </div>
                        <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                            {displayedFailures.map((failure, index) => (
                                <FailureLink
                                    key={failure.instanceId}
                                    runId={runId || ''}
                                    instanceId={failure.instanceId}
                                    scenarioId={failure.scenarioId}
                                    isNew={index === 0 && liveFailures.length > 1}
                                />
                            ))}
                        </div>
                        {liveFailures.length > 5 && !showAllFailures && (
                            <button
                                onClick={() => setShowAllFailures(true)}
                                className="w-full py-2 text-[10px] font-bold text-cyan-400 hover:text-cyan-300 transition-colors"
                            >
                                View All ({liveFailures.length - 5} more)
                            </button>
                        )}
                    </div>
                )}
            </div>

            {/* Top Failures Section */}
            {run && run.failures && run.failures.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 flex items-center gap-3">
                        Recurrent Failure Signatures
                        <div className="h-px flex-1 bg-white/5"></div>
                    </h2>
                    <div className="glass rounded-3xl overflow-hidden shadow-xl border-rose-500/10">
                        <div className="grid grid-cols-12 gap-6 px-8 py-4 bg-rose-500/[0.03] border-b border-white/5 text-[10px] font-black text-rose-500/60 uppercase tracking-widest">
                            <div className="col-span-8">Exception / Assertion Signature</div>
                            <div className="col-span-2 text-right">Frequency</div>
                            <div className="col-span-2 text-right">Distribution</div>
                        </div>
                        <div className="divide-y divide-white/5">
                            {run.failures.map((failure, i) => (
                                <div key={i} className="grid grid-cols-12 gap-6 px-8 py-5 items-center glass-hover">
                                    <div className="col-span-8 font-mono text-xs text-rose-300 break-all leading-relaxed">
                                        {failure.message}
                                    </div>
                                    <div className="col-span-2 text-right text-sm font-bold text-white tracking-tight">
                                        {failure.count}
                                    </div>
                                    <div className="col-span-2 text-right">
                                        <span className="text-[10px] font-black text-slate-500 bg-white/5 px-2 py-1 rounded">
                                            {failure.percentage.toFixed(1)}%
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Data Explorer */}
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">
                        Instance Explorer
                    </h2>
                    {/* Filter Bar */}
                    <div className="flex gap-1.5 p-1 rounded-xl bg-white/[0.03] border border-white/5">
                        {(['all', 'passed', 'failed', 'errors'] as FilterType[]).map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-300 ${filter === f
                                    ? 'bg-cyan-500 text-black shadow-[0_0_15px_rgba(6,182,212,0.4)]'
                                    : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                                    }`}
                            >
                                {f}
                                {run && (
                                    <span className={`ml-2 opacity-50 ${filter === f ? 'text-black' : ''}`}>
                                        {f === 'all' ? displayStats.total :
                                            f === 'passed' ? displayStats.passed :
                                                f === 'failed' ? displayStats.failed :
                                                    displayStats.errors}
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Instance Grid */}
                <div className="glass rounded-3xl overflow-hidden shadow-2xl">
                    {/* Table Header */}
                    <div className="grid grid-cols-5 gap-6 px-8 py-4 bg-white/[0.02] border-b border-white/5 text-[10px] font-black text-slate-500 uppercase tracking-widest">
                        <div>Compute ID</div>
                        <div>Trace ID</div>
                        <div>Workflow Path</div>
                        <div>Latency</div>
                        <div className="text-right">State</div>
                    </div>

                    {/* Table Body */}
                    <div className="divide-y divide-white/5">
                        {instancesLoading ? (
                            <div>
                                {[...Array(10)].map((_, i) => (
                                    <SkeletonRow key={i} />
                                ))}
                            </div>
                        ) : instancesData?.instances?.length === 0 ? (
                            <div className="p-20 text-center text-slate-500 text-xs italic font-medium">
                                No telemetry data matches the selected matrix.
                            </div>
                        ) : (
                            instancesData?.instances?.map((instance) => (
                                <Link
                                    key={instance.instance_id}
                                    to={`/runs/${runId}/instances/${instance.instance_id}`}
                                    className="grid grid-cols-5 gap-6 px-8 py-5 items-center glass-hover transition-all duration-300 group"
                                >
                                    <div className="font-mono text-sm font-bold text-slate-300 group-hover:text-cyan-400 transition-colors">
                                        {instance.instance_id}
                                    </div>
                                    <div className="font-mono text-[10px] text-slate-500">
                                        {instance.correlation_id}
                                    </div>
                                    <div className="text-xs font-semibold text-slate-400 italic">
                                        {instance.scenario_id}
                                    </div>
                                    <div className="font-mono text-xs text-slate-400">
                                        {instance.duration_ms.toFixed(1)}ms
                                    </div>
                                    <div className="flex justify-end">
                                        <StatusBadge
                                            status={
                                                instance.error ? 'error' :
                                                    instance.passed ? 'passed' : 'failed'
                                            }
                                            size="sm"
                                        />
                                    </div>
                                </Link>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function formatDuration(ms: number): string {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    const seconds = ms / 1000;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
}
