/**
 * FlowLegend Component
 *
 * Legend explaining action type color coding.
 */

export function FlowLegend() {
    const items = [
        { type: 'http', label: 'HTTP Request', color: 'bg-cyan-500' },
        { type: 'wait', label: 'Wait/Poll', color: 'bg-amber-500' },
        { type: 'assert', label: 'Assertion', color: 'bg-emerald-500' },
    ];

    return (
        <div className="absolute bottom-4 left-4 z-10 glass rounded-xl px-4 py-3 flex items-center gap-4">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">
                Legend
            </span>
            <div className="h-4 w-px bg-white/10" />
            {items.map((item) => (
                <div key={item.type} className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                    <span className="text-[11px] font-medium text-slate-400">
                        {item.label}
                    </span>
                </div>
            ))}
        </div>
    );
}
