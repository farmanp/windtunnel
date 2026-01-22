import { Link } from 'react-router-dom';

/**
 * FailureLink Component
 * 
 * Clickable failure indicator for real-time failure list.
 * Navigates to instance timeline on click.
 */

interface FailureLinkProps {
    runId: string;
    instanceId: string;
    scenarioId: string;
    errorSnippet?: string;
    /** Whether this is a newly added failure (triggers entrance animation) */
    isNew?: boolean;
}

export function FailureLink({
    runId,
    instanceId,
    scenarioId,
    errorSnippet,
    isNew = false,
}: FailureLinkProps) {
    return (
        <Link
            to={`/runs/${runId}/instances/${instanceId}`}
            className={`
                block p-3 rounded-lg glass glass-hover border border-rose-500/10
                transition-all duration-300 group
                ${isNew ? 'animate-in slide-in-from-right-2 fade-in duration-500' : ''}
            `}
        >
            <div className="flex items-start gap-2">
                {/* Failure indicator */}
                <div className="flex-shrink-0 w-1.5 h-1.5 mt-1.5 rounded-full bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.5)]" />

                <div className="flex-1 min-w-0">
                    {/* Instance ID */}
                    <p className="font-mono text-xs font-bold text-rose-300 group-hover:text-rose-200 transition-colors truncate">
                        {instanceId}
                    </p>

                    {/* Scenario */}
                    <p className="text-[10px] font-medium text-slate-500 truncate">
                        {scenarioId}
                    </p>

                    {/* Error snippet */}
                    {errorSnippet && (
                        <p className="mt-1 text-[10px] text-rose-400/60 font-mono truncate">
                            {errorSnippet}
                        </p>
                    )}
                </div>

                {/* Arrow icon */}
                <svg
                    className="flex-shrink-0 w-4 h-4 text-slate-500 group-hover:text-rose-400 group-hover:translate-x-0.5 transition-all"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
            </div>
        </Link>
    );
}
