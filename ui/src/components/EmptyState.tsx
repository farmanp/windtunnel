interface EmptyStateProps {
    title: string;
    description: string;
    icon?: React.ReactNode;
    action?: React.ReactNode;
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
            {icon && (
                <div className="w-16 h-16 rounded-full bg-[hsl(var(--color-bg-secondary))] flex items-center justify-center mb-4 text-[hsl(var(--color-text-secondary))]">
                    {icon}
                </div>
            )}
            <h3 className="text-lg font-medium text-[hsl(var(--color-text-primary))] mb-2">
                {title}
            </h3>
            <p className="text-sm text-[hsl(var(--color-text-secondary))] max-w-sm mb-6">
                {description}
            </p>
            {action}
        </div>
    );
}
