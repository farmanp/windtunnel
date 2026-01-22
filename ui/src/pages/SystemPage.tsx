export function SystemPage() {
    return (
        <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header */}
            <div className="flex flex-col gap-2">
                <h1 className="text-4xl font-bold tracking-tight text-white glow-cyan">
                    Engine Configuration
                </h1>
                <p className="text-sm font-medium text-slate-400">
                    <span className="text-slate-600 uppercase text-[10px] font-black tracking-widest mr-2">System Status</span>
                    Operational • Integrated with Local Filesystem
                </p>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Core Engine Card */}
                <div className="glass rounded-[2rem] p-8 border-white/5 shadow-2xl overflow-hidden relative group">
                    <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                        <svg className="w-24 h-24 text-cyan-400" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <h2 className="text-[10px] font-black uppercase tracking-[.3em] text-cyan-500 mb-6">Core Runtime</h2>
                    <div className="space-y-6">
                        <div className="flex justify-between items-center pb-4 border-b border-white/5">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Version</span>
                            <span className="font-mono text-xs text-white bg-white/5 px-2 py-1 rounded">v1.0.0-alpha</span>
                        </div>
                        <div className="flex justify-between items-center pb-4 border-b border-white/5">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Environment</span>
                            <span className="font-mono text-xs text-indigo-400">Production // Local</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Storage Backend</span>
                            <span className="font-mono text-xs text-slate-200">Local JSONL Artifacts</span>
                        </div>
                    </div>
                </div>

                {/* Telemetry Card */}
                <div className="glass rounded-[2rem] p-8 border-white/5 shadow-2xl relative group">
                    <h2 className="text-[10px] font-black uppercase tracking-[.3em] text-indigo-500 mb-6">Simulation telemetry</h2>
                    <div className="space-y-6">
                        <div className="flex justify-between items-center pb-4 border-b border-white/5">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Data Buffer</span>
                            <div className="flex items-center gap-2">
                                <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                    <div className="w-1/3 h-full bg-indigo-500"></div>
                                </div>
                                <span className="font-mono text-[10px] text-slate-500">32%</span>
                            </div>
                        </div>
                        <div className="flex justify-between items-center pb-4 border-b border-white/5">
                            <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Trace Retention</span>
                            <span className="text-xs font-bold text-white">30 Days</span>
                        </div>
                        <div className="flex items-center gap-3 mt-4 text-[10px] font-medium text-slate-500 italic">
                            <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Standard telemetry protocol active
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer Info */}
            <div className="p-8 glass rounded-[2rem] border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center">
                        <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <div>
                        <p className="text-xs font-bold text-white uppercase tracking-widest">Diagnostics Terminal</p>
                        <p className="text-[10px] text-slate-500 font-medium">All systems operating within normal parameters.</p>
                    </div>
                </div>
                <button className="px-6 py-2 rounded-xl bg-cyan-500/10 text-cyan-400 text-[10px] font-black uppercase tracking-widest hover:bg-cyan-500/20 transition-all">
                    Download Logs
                </button>
            </div>
        </div>
    );
}
