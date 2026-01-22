import { useEffect, useState, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

interface StreamMessage {
    type: 'instance_complete' | 'stats_update' | 'run_complete' | 'heartbeat' | 'error';
    data?: Record<string, unknown>;
}

interface UseRunStreamOptions {
    enabled?: boolean;
}

export function useRunStream(runId: string, options: UseRunStreamOptions = {}) {
    const { enabled = true } = options;
    const queryClient = useQueryClient();
    const [status, setStatus] = useState<ConnectionStatus>('disconnected');
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectDelay = 30000;

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
                    case 'instance_complete':
                        // Invalidate instances query to refetch
                        queryClient.invalidateQueries({ queryKey: ['runs', runId, 'instances'] });
                        break;

                    case 'stats_update':
                        // Update run stats in cache
                        queryClient.setQueryData(['runs', runId], (old: Record<string, unknown> | undefined) => {
                            if (!old) return old;
                            return {
                                ...old,
                                stats: message.data,
                            };
                        });
                        break;

                    case 'run_complete':
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
    }, [runId, enabled, queryClient]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
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
        connect();
    }, [disconnect, connect]);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        status,
        reconnect,
        disconnect,
    };
}
