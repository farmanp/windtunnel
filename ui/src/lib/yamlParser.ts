/**
 * YAML Parser Utility
 *
 * Client-side parsing of Turbulence scenarios using js-yaml.
 */

import yaml from 'js-yaml';

export interface Scenario {
    id: string;
    description?: string;
    flow: ScenarioStep[];
}

export interface ScenarioStep {
    name: string;
    type: 'http' | 'wait' | 'assert' | 'branch';
    // HTTP specific
    service?: string;
    method?: string;
    path?: string;
    extract?: Record<string, string>;
    // Wait specific
    interval_seconds?: number;
    timeout_seconds?: number;
    // Common
    expect?: {
        status_code?: number;
        jsonpath?: string;
        equals?: any;
        contains?: any;
    };
    [key: string]: any;
}

export interface ParseResult {
    scenario?: Scenario;
    error?: {
        message: string;
        line?: number;
    };
}

/**
 * Parse YAML string into a Scenario object.
 */
export function parseScenario(yamlContent: string): ParseResult {
    try {
        const data = yaml.load(yamlContent) as any;

        if (!data || typeof data !== 'object') {
            return { error: { message: 'Invalid YAML: Not an object' } };
        }

        if (!data.id) {
            return { error: { message: 'Missing required field: id' } };
        }

        if (!data.flow || !Array.isArray(data.flow)) {
            return { error: { message: 'Missing or invalid field: flow (must be an array)' } };
        }

        return {
            scenario: {
                id: data.id,
                description: data.description,
                flow: data.flow as ScenarioStep[],
            }
        };
    } catch (e: any) {
        return {
            error: {
                message: e.reason || e.message || 'Unknown YAML parse error',
                line: e.mark ? e.mark.line + 1 : undefined,
            }
        };
    }
}

/**
 * Get a friendly label for a step.
 */
export function getStepLabel(step: ScenarioStep): string {
    if (step.name) return step.name;

    switch (step.type) {
        case 'http':
            return `${step.method || 'GET'} ${step.path || '/'}`;
        case 'wait':
            return `Wait for ${step.path || 'condition'}`;
        case 'assert':
            return 'Assertion';
        default:
            return 'Unknown Action';
    }
}

/**
 * Get a short description for a step.
 */
export function getStepDescription(step: ScenarioStep): string {
    switch (step.type) {
        case 'http':
            return `${step.service ? `[${step.service}] ` : ''}${step.path || '/'}`;
        case 'wait':
            return `Until condition met (max ${step.timeout_seconds || 30}s)`;
        case 'assert':
            if (step.expect?.status_code) return `Expect status ${step.expect.status_code}`;
            if (step.expect?.jsonpath) return `Expect ${step.expect.jsonpath}`;
            return 'Validate state';
        default:
            return '';
    }
}