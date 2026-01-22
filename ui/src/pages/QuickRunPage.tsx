import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { ScenarioFlowPreview } from '@/components/ScenarioFlowPreview';

interface SutConfigSummary {
    name: string;
    path: string;
    file_name: string;
}

interface ScenarioSummary {
    id: string;
    description: string;
    path: string;
    file_name: string;
}

export function QuickRunPage() {
    const navigate = useNavigate();
    const [selectedSut, setSelectedSut] = useState('');
    const [selectedScenarios, setSelectedScenarios] = useState<string[]>([]);
    const [previewScenario, setPreviewScenario] = useState<string | null>(null);
    const [instances, setInstances] = useState(10);
    const [parallelism, setParallelism] = useState(5);
    const [launchError, setLaunchError] = useState<string | null>(null);
    const [isLaunching, setIsLaunching] = useState(false);

    const { data: sutData, isLoading: sutLoading } = useQuery<{ configs: SutConfigSummary[] }>({
        queryKey: ['sut-configs'],
        queryFn: async () => {
            const res = await fetch('/api/configs/sut');
            if (!res.ok) throw new Error('Failed to fetch SUT configs');
            return res.json();
        },
    });

    const { data: scenarioData, isLoading: scenarioLoading } = useQuery<{ scenarios: ScenarioSummary[] }>({
        queryKey: ['scenario-list'],
        queryFn: async () => {
            const res = await fetch('/api/configs/scenarios');
            if (!res.ok) throw new Error('Failed to fetch scenarios');
            return res.json();
        },
    });

    const { data: previewData, isLoading: previewLoading } = useQuery<{ content: string }>({
        queryKey: ['scenario-content', previewScenario],
        queryFn: async () => {
            const res = await fetch(`/api/configs/scenarios/content?path=${encodeURIComponent(previewScenario ?? '')}`);
            if (!res.ok) throw new Error('Failed to fetch scenario content');
            return res.json();
        },
        enabled: Boolean(previewScenario),
    });

    const scenarioMap = useMemo(() => {
        const map = new Map<string, ScenarioSummary>();
        scenarioData?.scenarios?.forEach((scenario) => {
            map.set(scenario.path, scenario);
        });
        return map;
    }, [scenarioData?.scenarios]);

    const canRun = selectedSut.length > 0 && selectedScenarios.length > 0 && !isLaunching;

    const toggleScenario = (scenarioPath: string) => {
        setSelectedScenarios((prev) => {
            if (prev.includes(scenarioPath)) {
                return prev.filter((path) => path !== scenarioPath);
            }
            return [...prev, scenarioPath];
        });
    };

    const handleRun = async () => {
        if (!canRun) {
            setLaunchError('Select a SUT config and at least one scenario before launching.');
            return;
        }
        setLaunchError(null);
        setIsLaunching(true);
        try {
            const res = await fetch('/api/runs/trigger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sut_path: selectedSut,
                    scenario_paths: selectedScenarios,
                    instances,
                    parallelism,
                }),
            });

            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(errorText || 'Run launch failed');
            }

            const data = await res.json();
            navigate(`/runs/${data.run_id}`);
        } catch (error) {
            setLaunchError(error instanceof Error ? error.message : 'Run launch failed');
        } finally {
            setIsLaunching(false);
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            <div className="flex items-end justify-between">
                <div>
                    <h1 className="text-4xl font-bold tracking-tight text-white glow-cyan mb-2">
                        Quick Run Launcher
                    </h1>
                    <p className="text-sm font-medium text-slate-500 uppercase tracking-widest">
                        Configure and launch simulations in seconds
                    </p>
                </div>
                <button
                    onClick={handleRun}
                    disabled={!canRun}
                    className={`px-6 py-3 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${canRun
                        ? 'glass glass-hover text-cyan-400'
                        : 'bg-white/5 text-slate-500 cursor-not-allowed'
                        }`}
                >
                    {isLaunching ? 'Launching…' : 'Run'}
                </button>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[380px_1fr] gap-8">
                <div className="space-y-6">
                    <div className="glass rounded-2xl p-6 space-y-4">
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-[.3em] text-slate-500 mb-2">
                                SUT Configuration
                            </p>
                            <select
                                value={selectedSut}
                                onChange={(event) => setSelectedSut(event.target.value)}
                                className="w-full bg-transparent border border-white/10 rounded-xl px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
                            >
                                <option value="">Select a SUT config</option>
                                {sutLoading ? (
                                    <option value="" disabled>Loading…</option>
                                ) : (
                                    sutData?.configs?.map((config) => (
                                        <option key={config.path} value={config.path}>
                                            {config.name} ({config.file_name})
                                        </option>
                                    ))
                                )}
                            </select>
                        </div>

                        <div>
                            <p className="text-[10px] font-black uppercase tracking-[.3em] text-slate-500 mb-2">
                                Scenarios
                            </p>
                            <div className="space-y-2 max-h-64 overflow-auto pr-2">
                                {scenarioLoading && (
                                    <div className="text-xs text-slate-500">Loading scenarios…</div>
                                )}
                                {!scenarioLoading && scenarioData?.scenarios?.length === 0 && (
                                    <div className="text-xs text-slate-500">No scenarios found.</div>
                                )}
                                {scenarioData?.scenarios?.map((scenario) => {
                                    const isSelected = selectedScenarios.includes(scenario.path);
                                    return (
                                        <div
                                            key={scenario.path}
                                            className={`flex items-start gap-3 rounded-xl border border-white/10 px-3 py-2 transition ${isSelected ? 'bg-white/10' : 'bg-white/5'
                                                }`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={isSelected}
                                                onChange={() => toggleScenario(scenario.path)}
                                                className="mt-1 h-4 w-4 accent-cyan-500"
                                            />
                                            <div className="flex-1">
                                                <p className="text-sm font-semibold text-slate-200">{scenario.id}</p>
                                                <p className="text-[10px] text-slate-500">{scenario.description || scenario.file_name}</p>
                                            </div>
                                            <button
                                                onClick={() => setPreviewScenario(scenario.path)}
                                                className="text-[10px] font-black uppercase tracking-widest text-cyan-400 hover:text-cyan-300"
                                            >
                                                Preview
                                            </button>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    <div className="glass rounded-2xl p-6 space-y-5">
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-[.3em] text-slate-500 mb-2">
                                Instance Count
                            </p>
                            <div className="flex items-center gap-3">
                                <input
                                    type="range"
                                    min={1}
                                    max={1000}
                                    value={instances}
                                    onChange={(event) => setInstances(Number(event.target.value))}
                                    className="flex-1"
                                />
                                <span className="text-xs font-mono text-cyan-400 w-12 text-right">
                                    {instances}
                                </span>
                            </div>
                        </div>
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-[.3em] text-slate-500 mb-2">
                                Parallelism
                            </p>
                            <div className="flex items-center gap-3">
                                <input
                                    type="range"
                                    min={1}
                                    max={100}
                                    value={parallelism}
                                    onChange={(event) => setParallelism(Number(event.target.value))}
                                    className="flex-1"
                                />
                                <span className="text-xs font-mono text-indigo-400 w-12 text-right">
                                    {parallelism}
                                </span>
                            </div>
                        </div>
                    </div>

                    {launchError && (
                        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-xs text-rose-400">
                            {launchError}
                        </div>
                    )}
                </div>

                <div className="space-y-4 min-h-[520px]">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-[.3em] text-slate-500">
                                Scenario Preview
                            </p>
                            <p className="text-xs text-slate-400">
                                {previewScenario ? scenarioMap.get(previewScenario)?.id : 'No scenario selected'}
                            </p>
                        </div>
                        {previewLoading && (
                            <span className="text-[10px] text-slate-500">Rendering…</span>
                        )}
                    </div>
                    <div className="h-[520px]">
                        <ScenarioFlowPreview yaml={previewData?.content ?? null} />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default QuickRunPage;
