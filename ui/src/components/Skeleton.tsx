interface SkeletonProps {
    className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
    return (
        <div
            className={`animate-pulse bg-white/[0.03] rounded-lg ${className}`}
        />
    );
}

export function SkeletonRow() {
    return (
        <div className="grid grid-cols-5 gap-6 px-8 py-5 items-center">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-48" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16" />
            <div className="flex justify-end">
                <Skeleton className="h-6 w-20 rounded-md" />
            </div>
        </div>
    );
}

export function SkeletonCard() {
    return (
        <div className="glass rounded-3xl p-6 border-white/5 shadow-xl">
            <Skeleton className="h-3 w-16 mb-4" />
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-3 w-32 mt-4" />
        </div>
    );
}
