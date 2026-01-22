/**
 * ProgressBar Component
 * 
 * Animated progress bar for live run monitoring with pass/fail breakdown.
 */

interface ProgressBarProps {
    /** Total number of instances (null = unknown/still loading) */
    total: number | null;
    /** Number of completed instances */
    completed: number;
    /** Number of passed instances */
    passed: number;
    /** Number of failed instances */
    failed: number;
    /** Whether we're still connecting to the stream */
    isConnecting?: boolean;
    /** Show pass/fail/pending counts below the bar */
    showCounts?: boolean;
    /** Size variant */
    size?: 'sm' | 'md';
}

export function ProgressBar({
    total,
    completed,
    passed,
    failed,
    isConnecting = false,
    showCounts = true,
    size = 'md',
}: ProgressBarProps) {
    const pending = total !== null ? total - completed : 0;
    const percentage = total !== null && total > 0 ? Math.round((completed / total) * 100) : 0;
    const isComplete = total !== null && completed >= total;

    // Size-based classes
    const barHeight = size === 'sm' ? 'h-1.5' : 'h-2.5';
    const textSize = size === 'sm' ? 'text-[9px]' : 'text-[10px]';
    const countTextSize = size === 'sm' ? 'text-[10px]' : 'text-xs';

    // Calculate segment widths
    const passedWidth = total !== null && total > 0 ? (passed / total) * 100 : 0;
    const failedWidth = total !== null && total > 0 ? (failed / total) * 100 : 0;

    return (
        <div className="w-full space-y-2">
            {/* Progress bar container */}
            <div className="flex items-center gap-3">
                <div className={`flex-1 ${barHeight} rounded-full bg-white/5 overflow-hidden relative`}>
                    {isConnecting ? (
                        // Indeterminate loading state
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent animate-shimmer" />
                    ) : (
                        // Segmented progress
                        <div className="flex h-full">
                            {/* Passed segment */}
                            <div
                                className={`h-full bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500 ease-out ${isComplete ? 'shadow-[0_0_12px_rgba(16,185,129,0.5)]' : ''
                                    }`}
                                style={{ width: `${passedWidth}%` }}
                            />
                            {/* Failed segment */}
                            <div
                                className="h-full bg-gradient-to-r from-rose-500 to-rose-400 transition-all duration-500 ease-out"
                                style={{ width: `${failedWidth}%` }}
                            />
                        </div>
                    )}
                </div>

                {/* Percentage label */}
                <span className={`${textSize} font-black tracking-widest tabular-nums ${isComplete
                        ? 'text-emerald-400'
                        : isConnecting
                            ? 'text-slate-500 animate-pulse'
                            : 'text-slate-300'
                    }`}>
                    {isConnecting ? '—%' : `${percentage}%`}
                </span>
            </div>

            {/* Counts breakdown */}
            {showCounts && (
                <div className={`flex items-center gap-4 ${countTextSize} font-bold tracking-wide`}>
                    {/* Passed */}
                    <span className="flex items-center gap-1.5 text-emerald-400">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="tabular-nums">{passed}</span>
                        <span className="text-slate-500 font-medium">Passed</span>
                    </span>

                    {/* Failed */}
                    <span className="flex items-center gap-1.5 text-rose-400">
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        <span className="tabular-nums">{failed}</span>
                        <span className="text-slate-500 font-medium">Failed</span>
                    </span>

                    {/* Pending */}
                    {total !== null && pending > 0 && (
                        <span className="flex items-center gap-1.5 text-slate-400">
                            <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <span className="tabular-nums">{pending}</span>
                            <span className="text-slate-500 font-medium">Pending</span>
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}
