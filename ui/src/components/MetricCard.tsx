interface MetricCardProps {
    label: string;
    value: string | number;
    sublabel?: string;
    variant?: 'default' | 'success' | 'failure' | 'warning';
}

const variantClasses = {
    default: 'text-[hsl(var(--color-text-primary))]',
    success: 'text-green-400',
    failure: 'text-red-400',
    warning: 'text-amber-400',
};

export function MetricCard({ label, value, sublabel, variant = 'default' }: MetricCardProps) {
    return (
        <div className="bg-[hsl(var(--color-bg-secondary))] rounded-xl p-5 border border-[hsl(var(--color-border))]">
            <p className="text-sm text-[hsl(var(--color-text-secondary))] mb-1">{label}</p>
            <p className={`text-3xl font-semibold ${variantClasses[variant]}`}>{value}</p>
            {sublabel && (
                <p className="text-xs text-[hsl(var(--color-text-secondary))] mt-1">{sublabel}</p>
            )}
        </div>
    );
}
