interface StatusBadgeProps {
    status: 'passed' | 'failed' | 'running' | 'error';
    size?: 'sm' | 'md';
}

const statusConfig = {
    passed: {
        bg: 'bg-green-500/20',
        text: 'text-green-400',
        label: 'Passed',
        icon: '✓',
    },
    failed: {
        bg: 'bg-red-500/20',
        text: 'text-red-400',
        label: 'Failed',
        icon: '✗',
    },
    running: {
        bg: 'bg-blue-500/20',
        text: 'text-blue-400',
        label: 'Running',
        icon: '◉',
    },
    error: {
        bg: 'bg-amber-500/20',
        text: 'text-amber-400',
        label: 'Error',
        icon: '!',
    },
};

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
    const config = statusConfig[status];
    const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

    return (
        <span
            className={`inline-flex items-center gap-1.5 rounded-full font-medium ${config.bg} ${config.text} ${sizeClasses}`}
        >
            <span className={status === 'running' ? 'animate-pulse' : ''}>
                {config.icon}
            </span>
            {config.label}
        </span>
    );
}
