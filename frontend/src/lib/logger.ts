/**
 * Logger — captura errores frontend, errores API y tiempos de respuesta.
 *
 * Preparado para integración futura con Sentry o similar.
 * NO instalar Sentry todavía.
 */

type LogLevel = "info" | "warn" | "error";

interface LogEntry {
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
  timestamp: string;
}

function createEntry(
  level: LogLevel,
  message: string,
  context?: Record<string, unknown>,
): LogEntry {
  return {
    level,
    message,
    context,
    timestamp: new Date().toISOString(),
  };
}

function serialize(entry: LogEntry): string {
  try {
    return JSON.stringify(entry);
  } catch {
    return `${entry.timestamp} [${entry.level}] ${entry.message}`;
  }
}

function logToConsole(entry: LogEntry): void {
  const { level, message, context } = entry;
  const extra = context ? ` ${JSON.stringify(context)}` : "";
  switch (level) {
    case "error":
      console.error(`[Contraduría] ${message}${extra}`);
      break;
    case "warn":
      console.warn(`[Contraduría] ${message}${extra}`);
      break;
    default:
      console.info(`[Contraduría] ${message}${extra}`);
  }
}

// Historial en memoria (solo últimas 50 entradas)
const MAX_ENTRIES = 50;
const _logHistory: LogEntry[] = [];

function push(entry: LogEntry): void {
  _logHistory.push(entry);
  if (_logHistory.length > MAX_ENTRIES) {
    _logHistory.shift();
  }
}

export const logger = {
  /** Obtener historial de logs (para debug) */
  getHistory(): LogEntry[] {
    return [..._logHistory];
  },

  info(message: string, context?: Record<string, unknown>): void {
    const entry = createEntry("info", message, context);
    push(entry);
    logToConsole(entry);
  },

  warn(message: string, context?: Record<string, unknown>): void {
    const entry = createEntry("warn", message, context);
    push(entry);
    logToConsole(entry);
  },

  error(
    message: string,
    errorOrContext?: Error | Record<string, unknown>,
  ): void {
    let context: Record<string, unknown> = {};
    if (errorOrContext instanceof Error) {
      context = {
        name: errorOrContext.name,
        message: errorOrContext.message,
        stack: errorOrContext.stack?.slice(0, 500),
      };
    } else if (errorOrContext) {
      context = errorOrContext;
    }
    const entry = createEntry("error", message, context);
    push(entry);
    logToConsole(entry);
  },

  /** Capturar errores de API con tiempo de respuesta */
  apiError(
    url: string,
    status: number,
    durationMs: number,
    errorBody?: unknown,
  ): void {
    logger.error(`API error ${status} ${url}`, {
      url,
      status,
      duration_ms: durationMs,
      body: typeof errorBody === "string" ? errorBody.slice(0, 200) : undefined,
    });
  },

  /** Capturar tiempos de respuesta exitosos */
  apiSuccess(url: string, durationMs: number): void {
    if (durationMs > 3000) {
      logger.warn(`API lenta: ${url}`, { url, duration_ms: durationMs });
    }
  },

  /** Capturar errores de renderizado de React */
  componentError(
    componentName: string,
    error: Error,
    info?: { componentStack?: string },
  ): void {
    logger.error(`Component error in ${componentName}`, {
      component: componentName,
      name: error.name,
      message: error.message,
      componentStack: info?.componentStack?.slice(0, 500),
    });
  },

  /** Limpiar historial */
  clear(): void {
    _logHistory.length = 0;
  },
};