import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { useState } from 'react';
import { StatusBadge } from '@/components/StatusBadge';
import { MetricCard } from '@/components/MetricCard';
import { SkeletonRow, SkeletonCard } from '@/components/Skeleton';

type FilterType = 'all' | 'passed' | 'failed' | 'errors';

interface Instance {
    instance_id: string;
    correlation_id: string;
    scenario_id: string;
    passed: boolean | null;
    duration_ms: number;
    error: string | null;
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
}

export function RunDetailPage() {
    const { runId } = useParams<{ runId: string }>();
    const [filter, setFilter] = useState<FilterType>('all');

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
        <div>
            {/* Breadcrumb */}
            <nav className="text-sm text-[hsl(var(--color-text-secondary))] mb-4">
                <Link to="/" className="hover:text-[hsl(var(--color-text-primary))]">Runs</Link>
                <span className="mx-2">›</span>
                <span className="text-[hsl(var(--color-text-primary))]">{runId}</span>
            </nav>

            {/* Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-semibold text-[hsl(var(--color-text-primary))]">
                    {runId}
                </h1>
                {run && (
                    <p className="text-sm text-[hsl(var(--color-text-secondary))] mt-1">
                        {run.sut_name} • {run.scenarios.join(', ')}
                    </p>
                )}
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-4 gap-4 mb-8">
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
                            label="Pass Rate"
                            value={`${run.stats.pass_rate.toFixed(1)}%`}
                            variant={passRateVariant}
                        />
                        <MetricCard
                            label="Duration"
                            value={formatDuration(run.stats.duration_ms)}
                        />
                        <MetricCard
                            label="Instances"
                            value={run.stats.total}
                            sublabel={`${run.stats.passed} passed, ${run.stats.failed} failed`}
                        />
                        <MetricCard
                            label="Errors"
                            value={run.stats.errors}
                            variant={run.stats.errors > 0 ? 'warning' : 'default'}
                        />
                    </>
                )}
            </div>

            {/* Filter Bar */}
            <div className="flex gap-2 mb-4">
                {(['all', 'passed', 'failed', 'errors'] as FilterType[]).map((f) => (
                    <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f
                                ? 'bg-[hsl(var(--color-info))] text-white'
                                : 'bg-[hsl(var(--color-bg-secondary))] text-[hsl(var(--color-text-secondary))] hover:bg-[hsl(var(--color-bg-elevated))]'
                            }`}
                    >
                        {f.charAt(0).toUpperCase() + f.slice(1)}
                        {run && (
                            <span className="ml-2 opacity-70">
                                {f === 'all' ? run.stats.total :
                                    f === 'passed' ? run.stats.passed :
                                        f === 'failed' ? run.stats.failed :
                                            run.stats.errors}
                            </span>
                        )}
                    </button>
                ))}
            </div>

            {/* Instance Grid */}
            <div className="bg-[hsl(var(--color-bg-secondary))] rounded-xl border border-[hsl(var(--color-border))] overflow-hidden">
                {/* Table Header */}
                <div className="grid grid-cols-5 gap-4 px-6 py-3 bg-[hsl(var(--color-bg-elevated))] border-b border-[hsl(var(--color-border))] text-xs font-medium text-[hsl(var(--color-text-secondary))] uppercase tracking-wider">
                    <div>Instance ID</div>
                    <div>Correlation ID</div>
                    <div>Scenario</div>
                    <div>Duration</div>
                    <div>Status</div>
                </div>

                {/* Table Body */}
                {instancesLoading ? (
                    <div>
                        {[...Array(10)].map((_, i) => (
                            <SkeletonRow key={i} />
                        ))}
                    </div>
                ) : instancesData?.instances?.length === 0 ? (
                    <div className="p-8 text-center text-[hsl(var(--color-text-secondary))]">
                        No instances match the current filter.
                    </div>
                ) : (
                    instancesData?.instances?.map((instance) => (
                        <Link
                            key={instance.instance_id}
                            to={`/runs/${runId}/instances/${instance.instance_id}`}
                            className="grid grid-cols-5 gap-4 px-6 py-4 border-b border-[hsl(var(--color-border))] hover:bg-[hsl(var(--color-bg-elevated))] transition-colors cursor-pointer"
                        >
                            <div className="font-mono text-sm text-[hsl(var(--color-text-primary))]">
                                {instance.instance_id}
                            </div>
                            <div className="font-mono text-sm text-[hsl(var(--color-text-secondary))]">
                                {instance.correlation_id}
                            </div>
                            <div className="text-sm text-[hsl(var(--color-text-secondary))]">
                                {instance.scenario_id}
                            </div>
                            <div className="text-sm text-[hsl(var(--color-text-secondary))]">
                                {instance.duration_ms.toFixed(0)}ms
                            </div>
                            <div>
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
