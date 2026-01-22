interface SkeletonProps {
    className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
    return (
        <div
            className={`animate-pulse bg-[hsl(var(--color-bg-elevated))] rounded ${className}`}
        />
    );
}

export function SkeletonRow() {
    return (
        <div className="flex items-center gap-4 p-4 border-b border-[hsl(var(--color-border))]">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-6 w-20 rounded-full" />
        </div>
    );
}

export function SkeletonCard() {
    return (
        <div className="bg-[hsl(var(--color-bg-secondary))] rounded-xl p-5 border border-[hsl(var(--color-border))]">
            <Skeleton className="h-4 w-20 mb-2" />
            <Skeleton className="h-8 w-24" />
        </div>
    );
}
