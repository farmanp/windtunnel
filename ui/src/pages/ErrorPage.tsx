import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom';

export function ErrorPage() {
    const error = useRouteError();
    console.error(error);

    let title = 'Unexpected System Error';
    let message = 'The engine encountered an unhandled exception during navigation.';
    let code = 'ERROR_GENERIC';

    if (isRouteErrorResponse(error)) {
        if (error.status === 404) {
            title = 'Telemetry Ghost (404)';
            message = 'The requested coordinate does not exist in the current simulation space.';
            code = 'SIGNAL_LOST';
        } else {
            title = `Error ${error.status}`;
            message = error.statusText;
            code = 'RESPONSE_ANOMALY';
        }
    } else if (error instanceof Error) {
        message = error.message;
    }

    return (
        <div className="min-h-screen bg-[#05070a] flex items-center justify-center p-6 selection:bg-rose-500/30">
            {/* Background Ambience */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-rose-500/5 blur-[120px] rounded-full animate-pulse-subtle"></div>
                <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-indigo-500/5 blur-[120px] rounded-full"></div>
            </div>

            <div className="relative max-w-lg w-full">
                <div className="glass rounded-[2.5rem] p-12 text-center border-rose-500/10 shadow-2xl animate-in fade-in zoom-in duration-700">
                    {/* Diagnostic Icon */}
                    <div className="mb-8 flex justify-center">
                        <div className="w-24 h-24 rounded-3xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center relative group">
                            <div className="absolute inset-0 bg-rose-500/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>
                            <svg className="w-12 h-12 text-rose-500 relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                    </div>

                    <p className="text-[10px] font-black uppercase tracking-[.3em] text-rose-500 mb-2">
                        System Diagnostics // {code}
                    </p>

                    <h1 className="text-3xl font-bold text-white mb-4 tracking-tight">
                        {title}
                    </h1>

                    <p className="text-slate-400 text-sm leading-relaxed mb-10 font-medium">
                        {message}
                    </p>

                    <div className="flex flex-col gap-3">
                        <Link
                            to="/"
                            className="px-8 py-4 rounded-2xl bg-white/5 border border-white/10 text-white font-bold text-xs uppercase tracking-widest hover:bg-white/10 hover:border-cyan-500/30 transition-all duration-300"
                        >
                            Return to Command Center
                        </Link>
                        <button
                            onClick={() => window.location.reload()}
                            className="px-8 py-4 text-slate-500 font-bold text-[10px] uppercase tracking-[.2em] hover:text-cyan-400 transition-colors"
                        >
                            Force Engine Reboot
                        </button>
                    </div>
                </div>

                {/* Footer Decal */}
                <div className="mt-8 flex justify-center opacity-20 pointer-events-none">
                    <p className="text-[10px] font-black uppercase tracking-[.5em] text-slate-500">
                        Windtunnel Simulation Engine v1.0
                    </p>
                </div>
            </div>
        </div>
    );
}
