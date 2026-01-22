interface EmptyStateProps {
    title: string;
    description: string;
    icon?: React.ReactNode;
    action?: React.ReactNode;
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center py-24 text-center animate-in fade-in zoom-in-95 duration-700">
            {icon && (
                <div className="w-20 h-20 rounded-3xl glass border-white/5 flex items-center justify-center mb-6 text-slate-600 shadow-2xl">
                    {icon}
                </div>
            )}
            <h3 className="text-xl font-bold text-white mb-2 tracking-tight group-hover:glow-cyan transition-all">
                {title}
            </h3>
            <p className="text-xs font-medium text-slate-500 max-w-xs mb-8 uppercase tracking-widest leading-relaxed">
                {description}
            </p>
            {action}
        </div>
    );
}
