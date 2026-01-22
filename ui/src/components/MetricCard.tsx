interface MetricCardProps {
    label: string;
    value: string | number;
    sublabel?: string;
    tooltip?: string;
    variant?: 'default' | 'success' | 'failure' | 'warning';
}

const variantClasses = {
    default: 'text-white glow-cyan',
    success: 'text-emerald-400 glow-pass',
    failure: 'text-rose-400 glow-fail',
    warning: 'text-amber-400',
};

export function MetricCard({ label, value, sublabel, tooltip, variant = 'default' }: MetricCardProps) {
    return (
        <div className="glass glass-hover rounded-2xl p-6 transition-all duration-500 relative group overflow-hidden">
            {/* Background illumination effect */}
            <div className={`absolute -right-4 -top-8 w-24 h-24 blur-3xl opacity-20 transition-opacity group-hover:opacity-40 rounded-full ${variant === 'success' ? 'bg-emerald-500' : variant === 'failure' ? 'bg-rose-500' : 'bg-cyan-500'}`} />

            <div className="flex items-center gap-2 mb-2">
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</p>
                {tooltip && (
                    <div className="text-slate-500 hover:text-cyan-400 transition-colors cursor-help" title={tooltip}>
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                )}
            </div>

            <p className={`text-3xl font-bold tracking-tight mb-2 ${variantClasses[variant]}`}>{value}</p>

            {sublabel && (
                <p className="text-xs font-medium text-slate-500 leading-relaxed">{sublabel}</p>
            )}
        </div>
    );
}
