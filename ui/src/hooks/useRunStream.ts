import { useEffect, useState, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

export interface LiveStats {
    /** Number of completed instances */
    completed: number;
    /** Number of passed instances */
    passed: number;
    /** Number of failed instances */
    failed: number;
    /** Number of error instances */
    errors: number;
    /** Pass rate percentage */
    passRate: number;
}

export interface FailedInstance {
    instanceId: string;
    scenarioId: string;
    correlationId: string;
    durationMs: number;
    timestamp: number;
}

interface StreamMessage {
    type: 'instance_complete' | 'stats_update' | 'run_complete' | 'heartbeat' | 'error';
    data?: Record<string, unknown>;
}

interface UseRunStreamOptions {
    enabled?: boolean;
    /** Throttle interval in ms for UI updates (default: 100) */
    throttleMs?: number;
}

export function useRunStream(runId: string, options: UseRunStreamOptions = {}) {
    const { enabled = true, throttleMs = 100 } = options;
    const queryClient = useQueryClient();
    const [status, setStatus] = useState<ConnectionStatus>('disconnected');
    const [liveStats, setLiveStats] = useState<LiveStats>({
        completed: 0,
        passed: 0,
        failed: 0,
        errors: 0,
        passRate: 0,
    });
    const [failures, setFailures] = useState<FailedInstance[]>([]);
    const [isComplete, setIsComplete] = useState(false);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectDelay = 30000;

    // Throttle state for batch updates
    const pendingStatsRef = useRef<LiveStats | null>(null);
    const pendingFailuresRef = useRef<FailedInstance[]>([]);
    const throttleTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

    const flushUpdates = useCallback(() => {
        if (pendingStatsRef.current) {
            setLiveStats(pendingStatsRef.current);
            pendingStatsRef.current = null;
        }
        if (pendingFailuresRef.current.length > 0) {
            setFailures(prev => [...prev, ...pendingFailuresRef.current]);
            pendingFailuresRef.current = [];
        }
    }, []);

    const scheduleFlush = useCallback(() => {
        if (!throttleTimerRef.current) {
            throttleTimerRef.current = setTimeout(() => {
                flushUpdates();
                throttleTimerRef.current = undefined;
            }, throttleMs);
        }
    }, [flushUpdates, throttleMs]);

    const connect = useCallback(() => {
        if (!enabled || !runId) return;

        const wsUrl = `ws://localhost:8000/api/runs/${runId}/stream`;
        setStatus('connecting');

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setStatus('connected');
            reconnectAttemptsRef.current = 0;
        };

        ws.onmessage = (event) => {
            try {
                const message: StreamMessage = JSON.parse(event.data);

                switch (message.type) {
                    case 'instance_complete': {
                        const data = message.data as {
                            instanceId?: string;
                            correlationId?: string;
                            scenarioId?: string;
                            passed?: boolean;
                            durationMs?: number;
                        };

                        // Track failed instances
                        if (data && data.passed === false) {
                            pendingFailuresRef.current.push({
                                instanceId: data.instanceId || '',
                                scenarioId: data.scenarioId || '',
                                correlationId: data.correlationId || '',
                                durationMs: data.durationMs || 0,
                                timestamp: Date.now(),
                            });
                            scheduleFlush();
                        }

                        // Invalidate instances query to refetch
                        queryClient.invalidateQueries({ queryKey: ['runs', runId, 'instances'] });
                        break;
                    }

                    case 'stats_update': {
                        const data = message.data as {
                            total?: number;
                            passed?: number;
                            failed?: number;
                            passRate?: number;
                        };

                        if (data) {
                            const completed = (data.passed || 0) + (data.failed || 0);
                            pendingStatsRef.current = {
                                completed,
                                passed: data.passed || 0,
                                failed: data.failed || 0,
                                errors: 0, // Backend doesn't separate errors yet
                                passRate: data.passRate || 0,
                            };
                            scheduleFlush();
                        }

                        // Update run stats in cache
                        queryClient.setQueryData(['runs', runId], (old: Record<string, unknown> | undefined) => {
                            if (!old) return old;
                            return {
                                ...old,
                                stats: message.data,
                            };
                        });
                        break;
                    }

                    case 'run_complete':
                        // Flush any pending updates immediately
                        flushUpdates();
                        setIsComplete(true);

                        // Invalidate all queries for this run
                        queryClient.invalidateQueries({ queryKey: ['runs', runId] });
                        queryClient.invalidateQueries({ queryKey: ['runs'] });
                        break;

                    case 'heartbeat':
                        // Keep-alive, no action needed
                        break;

                    case 'error':
                        console.error('[useRunStream] Server error:', message.data);
                        break;
                }
            } catch (err) {
                console.error('[useRunStream] Failed to parse message:', err);
            }
        };

        ws.onclose = () => {
            setStatus('disconnected');
            wsRef.current = null;

            // Don't reconnect if run is complete
            if (isComplete) return;

            // Auto-reconnect with exponential backoff
            const delay = Math.min(
                1000 * Math.pow(2, reconnectAttemptsRef.current),
                maxReconnectDelay
            );
            reconnectAttemptsRef.current += 1;

            reconnectTimeoutRef.current = setTimeout(() => {
                connect();
            }, delay);
        };

        ws.onerror = (error) => {
            console.error('[useRunStream] WebSocket error:', error);
        };
    }, [runId, enabled, queryClient, scheduleFlush, flushUpdates, isComplete]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (throttleTimerRef.current) {
            clearTimeout(throttleTimerRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setStatus('disconnected');
    }, []);

    const reconnect = useCallback(() => {
        disconnect();
        reconnectAttemptsRef.current = 0;
        // Reset state on manual reconnect
        setLiveStats({
            completed: 0,
            passed: 0,
            failed: 0,
            errors: 0,
            passRate: 0,
        });
        setFailures([]);
        setIsComplete(false);
        connect();
    }, [disconnect, connect]);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        status,
        liveStats,
        failures,
        isComplete,
        reconnect,
        disconnect,
    };
}
