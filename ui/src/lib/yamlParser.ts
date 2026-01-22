/**
 * YAML Scenario Parser
 *
 * Parses Turbulence scenario YAML files into typed structures for visualization.
 */

import yaml from 'js-yaml';

// ============================================================================
// Type Definitions
// ============================================================================

export interface HttpStep {
    type: 'http';
    name: string;
    service: string;
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    path: string;
    headers?: Record<string, string>;
    query?: Record<string, string>;
    body?: unknown;
    extract?: Record<string, string>;
}

export interface WaitStep {
    type: 'wait';
    name: string;
    service: string;
    path: string;
    interval_seconds: number;
    timeout_seconds: number;
    expect?: {
        jsonpath?: string;
        equals?: string;
    };
}

export interface AssertStep {
    type: 'assert';
    name: string;
    expect: {
        status_code?: number;
        jsonpath?: string;
        equals?: string;
        expression?: string;
        schema?: unknown;
    };
}

export type ScenarioStep = HttpStep | WaitStep | AssertStep;

export interface Scenario {
    id: string;
    description?: string;
    flow: ScenarioStep[];
    assertions?: Array<{
        name: string;
        expect: Record<string, unknown>;
    }>;
    stop_when?: {
        any_action_fails?: boolean;
    };
}

export interface ParseError {
    message: string;
    line?: number;
    column?: number;
}

export interface ParseResult {
    scenario?: Scenario;
    error?: ParseError;
}

// ============================================================================
// Parser Functions
// ============================================================================

/**
 * Parse a YAML string into a Scenario object.
 *
 * @param yamlContent - Raw YAML string
 * @returns ParseResult with either scenario or error
 */
export function parseScenario(yamlContent: string): ParseResult {
    if (!yamlContent.trim()) {
        return {
            error: {
                message: 'Empty YAML content',
            },
        };
    }

    try {
        const parsed = yaml.load(yamlContent) as Record<string, unknown>;

        if (!parsed || typeof parsed !== 'object') {
            return {
                error: {
                    message: 'Invalid YAML: must be an object',
                },
            };
        }

        // Validate required fields
        if (!parsed.id || typeof parsed.id !== 'string') {
            return {
                error: {
                    message: 'Missing required field: id',
                },
            };
        }

        if (!parsed.flow || !Array.isArray(parsed.flow)) {
            return {
                error: {
                    message: 'Missing required field: flow (must be an array)',
                },
            };
        }

        // Validate and type each step
        const flow: ScenarioStep[] = [];
        for (let i = 0; i < parsed.flow.length; i++) {
            const step = parsed.flow[i] as Record<string, unknown>;
            const validated = validateStep(step, i);
            if (validated.error) {
                return { error: validated.error };
            }
            if (validated.step) {
                flow.push(validated.step);
            }
        }

        const scenario: Scenario = {
            id: parsed.id as string,
            description: parsed.description as string | undefined,
            flow,
            assertions: parsed.assertions as Scenario['assertions'],
            stop_when: parsed.stop_when as Scenario['stop_when'],
        };

        return { scenario };
    } catch (err) {
        if (err instanceof yaml.YAMLException) {
            return {
                error: {
                    message: err.message,
                    line: err.mark?.line ? err.mark.line + 1 : undefined,
                    column: err.mark?.column ? err.mark.column + 1 : undefined,
                },
            };
        }

        return {
            error: {
                message: err instanceof Error ? err.message : 'Unknown parse error',
            },
        };
    }
}

function validateStep(
    step: Record<string, unknown>,
    index: number
): { step?: ScenarioStep; error?: ParseError } {
    if (!step.type || typeof step.type !== 'string') {
        return {
            error: {
                message: `Step ${index + 1}: missing or invalid 'type' field`,
            },
        };
    }

    if (!step.name || typeof step.name !== 'string') {
        return {
            error: {
                message: `Step ${index + 1}: missing or invalid 'name' field`,
            },
        };
    }

    switch (step.type) {
        case 'http':
            return { step: step as unknown as HttpStep };
        case 'wait':
            return { step: step as unknown as WaitStep };
        case 'assert':
            return { step: step as unknown as AssertStep };
        default:
            return {
                error: {
                    message: `Step ${index + 1}: unknown type '${step.type}'`,
                },
            };
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get the display label for a step.
 */
export function getStepLabel(step: ScenarioStep): string {
    return step.name.replace(/_/g, ' ');
}

/**
 * Get a short description for a step.
 */
export function getStepDescription(step: ScenarioStep): string {
    switch (step.type) {
        case 'http':
            return `${step.method} ${step.path}`;
        case 'wait':
            return `Poll ${step.path} (${step.timeout_seconds}s)`;
        case 'assert':
            if (step.expect.status_code) {
                return `Status = ${step.expect.status_code}`;
            }
            if (step.expect.jsonpath) {
                return `${step.expect.jsonpath}`;
            }
            return 'Assertion';
    }
}

/**
 * Extract template variables from a string.
 */
export function extractTemplateVars(text: string): string[] {
    const matches = text.match(/\{\{([^}]+)\}\}/g) || [];
    return matches.map((m) => m.slice(2, -2).trim());
}
