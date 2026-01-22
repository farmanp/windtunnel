import { useEffect, useState, useRef, useCallback } from 'react';
import type { LiveStats, ConnectionStatus } from './useRunStream';

export interface RunStreamState {
    status: ConnectionStatus;
    liveStats: LiveStats;
}

interface UseMultiRunStreamOptions {
    /** Only subscribe to runs that are still active (no completed_at) */
    activeOnly?: boolean;
}

/**
 * Hook for subscribing to multiple run streams simultaneously.
 * Used on the run list page to show live progress for all active runs.
 */
export function useMultiRunStream(
    runIds: string[],
    _options: UseMultiRunStreamOptions = {}
) {
    const [streams, setStreams] = useState<Map<string, RunStreamState>>(new Map());
    const wsRefs = useRef<Map<string, WebSocket>>(new Map());
    const reconnectTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

    const connectToRun = useCallback((runId: string) => {
        // Don't reconnect if already connected
        if (wsRefs.current.has(runId)) return;

        const wsUrl = `ws://localhost:8000/api/runs/${runId}/stream`;
        const ws = new WebSocket(wsUrl);
        wsRefs.current.set(runId, ws);

        // Initialize stream state
        setStreams(prev => {
            const next = new Map(prev);
            next.set(runId, {
                status: 'connecting',
                liveStats: {
                    completed: 0,
                    passed: 0,
                    failed: 0,
                    errors: 0,
                    passRate: 0,
                },
            });
            return next;
        });

        ws.onopen = () => {
            setStreams(prev => {
                const next = new Map(prev);
                const current = next.get(runId);
                if (current) {
                    next.set(runId, { ...current, status: 'connected' });
                }
                return next;
            });
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);

                if (message.type === 'stats_update' && message.data) {
                    const data = message.data as {
                        passed?: number;
                        failed?: number;
                        passRate?: number;
                    };
                    const completed = (data.passed || 0) + (data.failed || 0);

                    setStreams(prev => {
                        const next = new Map(prev);
                        const current = next.get(runId);
                        if (current) {
                            next.set(runId, {
                                ...current,
                                liveStats: {
                                    completed,
                                    passed: data.passed || 0,
                                    failed: data.failed || 0,
                                    errors: 0,
                                    passRate: data.passRate || 0,
                                },
                            });
                        }
                        return next;
                    });
                }

                if (message.type === 'run_complete') {
                    // Close connection when run completes
                    ws.close();
                    wsRefs.current.delete(runId);
                    setStreams(prev => {
                        const next = new Map(prev);
                        next.delete(runId);
                        return next;
                    });
                }
            } catch (err) {
                console.error(`[useMultiRunStream] Failed to parse message for ${runId}:`, err);
            }
        };

        ws.onclose = () => {
            wsRefs.current.delete(runId);
            setStreams(prev => {
                const next = new Map(prev);
                const current = next.get(runId);
                if (current) {
                    next.set(runId, { ...current, status: 'disconnected' });
                }
                return next;
            });

            // Auto-reconnect after 5 seconds if still in runIds
            const timer = setTimeout(() => {
                reconnectTimers.current.delete(runId);
                if (runIds.includes(runId)) {
                    connectToRun(runId);
                }
            }, 5000);
            reconnectTimers.current.set(runId, timer);
        };

        ws.onerror = (error) => {
            console.error(`[useMultiRunStream] WebSocket error for ${runId}:`, error);
        };
    }, [runIds]);

    const disconnectFromRun = useCallback((runId: string) => {
        const ws = wsRefs.current.get(runId);
        if (ws) {
            ws.close();
            wsRefs.current.delete(runId);
        }

        const timer = reconnectTimers.current.get(runId);
        if (timer) {
            clearTimeout(timer);
            reconnectTimers.current.delete(runId);
        }

        setStreams(prev => {
            const next = new Map(prev);
            next.delete(runId);
            return next;
        });
    }, []);

    // Manage subscriptions based on runIds
    useEffect(() => {
        const currentIds = new Set(runIds);
        const connectedIds = new Set(wsRefs.current.keys());

        // Connect to new runs
        for (const runId of currentIds) {
            if (!connectedIds.has(runId)) {
                connectToRun(runId);
            }
        }

        // Disconnect from removed runs
        for (const runId of connectedIds) {
            if (!currentIds.has(runId)) {
                disconnectFromRun(runId);
            }
        }
    }, [runIds, connectToRun, disconnectFromRun]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            for (const ws of wsRefs.current.values()) {
                ws.close();
            }
            wsRefs.current.clear();

            for (const timer of reconnectTimers.current.values()) {
                clearTimeout(timer);
            }
            reconnectTimers.current.clear();
        };
    }, []);

    return {
        streams,
        getStreamState: (runId: string) => streams.get(runId),
    };
}
