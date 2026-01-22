import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { useState } from 'react';
import { StatusBadge } from '@/components/StatusBadge';
import { MetricCard } from '@/components/MetricCard';
import { SkeletonRow, SkeletonCard } from '@/components/Skeleton';
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

    // Real-time streaming
    const { status: streamStatus, reconnect } = useRunStream(runId || '');

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

    const passRateVariant =
        (run?.stats.pass_rate ?? 0) >= 95 ? 'success' :
            (run?.stats.pass_rate ?? 0) >= 80 ? 'warning' :
                'failure';

    return (
        <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Breadcrumb */}
            <nav className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                <Link to="/" className="hover:text-cyan-400 transition-colors">Executions</Link>
                <span className="opacity-30">/</span>
                <span className="text-slate-300">{runId}</span>
            </nav>

            {/* Header */}
            <div className="flex flex-col gap-2">
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
                </div>
                {run && (
                    <p className="text-sm font-medium text-slate-400">
                        <span className="text-slate-600 uppercase text-[10px] font-black tracking-widest mr-2">System Under Test</span>
                        <span className="text-slate-200">{run.sut_name}</span>
                        <span className="mx-3 opacity-20">|</span>
                        <span className="text-slate-400 italic">{run.scenarios.join(' • ')}</span>
                    </p>
                )}
            </div>

            {/* Summary Cards */}
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
                            value={`${run.stats.pass_rate.toFixed(1)}%`}
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
                            value={run.stats.total}
                            sublabel={`${run.stats.passed} Passed • ${run.stats.failed} Failed`}
                            tooltip="The total number of concurrent instances spawned for this session."
                        />
                        <MetricCard
                            label="IO Errors"
                            value={run.stats.errors}
                            variant={run.stats.errors > 0 ? 'warning' : 'default'}
                            sublabel="Network / Host exceptions"
                            tooltip="Non-assertion failures. These represent infra stability issues rather than logic bugs."
                        />
                    </>
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
                                        {f === 'all' ? run.stats.total :
                                            f === 'passed' ? run.stats.passed :
                                                f === 'failed' ? run.stats.failed :
                                                    run.stats.errors}
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
