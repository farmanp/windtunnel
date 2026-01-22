import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { StatusBadge } from '@/components/StatusBadge';
import { EmptyState } from '@/components/EmptyState';
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
    });

    return (
        <div>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-semibold text-[hsl(var(--color-text-primary))]">
                        Runs
                    </h1>
                    <p className="text-sm text-[hsl(var(--color-text-secondary))] mt-1">
                        {data?.runs?.length ?? 0} runs
                    </p>
                </div>
                <button
                    onClick={() => refetch()}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[hsl(var(--color-bg-secondary))] hover:bg-[hsl(var(--color-bg-elevated))] text-[hsl(var(--color-text-secondary))] hover:text-[hsl(var(--color-text-primary))] transition-colors border border-[hsl(var(--color-border))]"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh
                </button>
            </div>

            {/* Table */}
            <div className="bg-[hsl(var(--color-bg-secondary))] rounded-xl border border-[hsl(var(--color-border))] overflow-hidden">
                {/* Table Header */}
                <div className="grid grid-cols-6 gap-4 px-6 py-3 bg-[hsl(var(--color-bg-elevated))] border-b border-[hsl(var(--color-border))] text-xs font-medium text-[hsl(var(--color-text-secondary))] uppercase tracking-wider">
                    <div>Run ID</div>
                    <div>SUT</div>
                    <div>Started</div>
                    <div>Duration</div>
                    <div>Pass Rate</div>
                    <div>Status</div>
                </div>

                {/* Table Body */}
                {isLoading ? (
                    <div>
                        {[...Array(5)].map((_, i) => (
                            <SkeletonRow key={i} />
                        ))}
                    </div>
                ) : error ? (
                    <div className="p-8 text-center text-red-400">
                        Failed to load runs. Is the API server running?
                    </div>
                ) : data?.runs?.length === 0 ? (
                    <EmptyState
                        title="No runs yet"
                        description="Run your first workflow simulation to see results here."
                        icon={
                            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                        }
                    />
                ) : (
                    data?.runs?.map((run) => (
                        <RunRow key={run.id} run={run} />
                    ))
                )}
            </div>
        </div>
    );
}

function RunRow({ run }: { run: Run }) {
    const passRate = run.stats.pass_rate;
    const passRateColor =
        passRate >= 95 ? 'text-green-400' :
            passRate >= 80 ? 'text-amber-400' :
                'text-red-400';

    const isRunning = run.completed_at === null;
    const status = isRunning ? 'running' : run.stats.failed > 0 ? 'failed' : 'passed';

    return (
        <Link
            to={`/runs/${run.id}`}
            className="grid grid-cols-6 gap-4 px-6 py-4 border-b border-[hsl(var(--color-border))] hover:bg-[hsl(var(--color-bg-elevated))] transition-colors cursor-pointer"
        >
            <div className="font-mono text-sm text-[hsl(var(--color-text-primary))]">
                {run.id}
            </div>
            <div className="text-sm text-[hsl(var(--color-text-secondary))]">
                {run.sut_name}
            </div>
            <div className="text-sm text-[hsl(var(--color-text-secondary))]">
                {formatRelativeTime(run.started_at)}
            </div>
            <div className="text-sm text-[hsl(var(--color-text-secondary))]">
                {formatDuration(run.stats.duration_ms)}
            </div>
            <div className="flex items-center gap-2">
                <div className="w-16 h-1.5 rounded-full bg-[hsl(var(--color-bg-elevated))] overflow-hidden">
                    <div
                        className={`h-full rounded-full ${passRate >= 95 ? 'bg-green-500' :
                                passRate >= 80 ? 'bg-amber-500' :
                                    'bg-red-500'
                            }`}
                        style={{ width: `${passRate}%` }}
                    />
                </div>
                <span className={`text-sm font-medium ${passRateColor}`}>
                    {passRate.toFixed(1)}%
                </span>
            </div>
            <div>
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
