interface StatusBadgeProps {
    status: 'passed' | 'failed' | 'running' | 'error';
    size?: 'sm' | 'md';
}

const statusConfig = {
    passed: {
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/20',
        text: 'text-emerald-400',
        label: 'Success',
        glow: 'shadow-[0_0_12px_rgba(16,185,129,0.2)]',
        icon: (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
        ),
    },
    failed: {
        bg: 'bg-rose-500/10',
        border: 'border-rose-500/20',
        text: 'text-rose-400',
        label: 'Failed',
        glow: 'shadow-[0_0_12px_rgba(244,63,94,0.2)]',
        icon: (
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
        ),
    },
    running: {
        bg: 'bg-cyan-500/10',
        border: 'border-cyan-500/20',
        text: 'text-cyan-400',
        label: 'Running',
        glow: 'shadow-[0_0_12px_rgba(6,182,212,0.2)]',
        icon: <div className="w-2 h-2 rounded-full bg-current animate-pulse" />,
    },
    error: {
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/20',
        text: 'text-amber-400',
        label: 'Error',
        glow: 'shadow-[0_0_12px_rgba(245,158,11,0.2)]',
        icon: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
        ),
    },
};

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
    const config = statusConfig[status];
    const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs';

    return (
        <span
            className={`inline-flex items-center gap-1.5 rounded-md border font-bold uppercase tracking-wider transition-all duration-300 ${config.bg} ${config.border} ${config.text} ${config.glow} ${sizeClasses}`}
        >
            <span className="flex-shrink-0">{config.icon}</span>
            {config.label}
        </span>
    );
}
