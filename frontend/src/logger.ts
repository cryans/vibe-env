const originalLog = console.log;
const originalError = console.error;
const originalWarn = console.warn;
const originalInfo = console.info;
const originalDebug = console.debug;

function sendLogToBackend(level: string, ...args: any[]) {
    try {
        const message = args.map(arg => {
            if (arg instanceof Error) {
                return arg.stack || arg.message;
            }
            if (typeof arg === 'object') {
                try {
                    return JSON.stringify(arg);
                } catch (e) {
                    return String(arg);
                }
            }
            return String(arg);
        }).join(' ');

        fetch(`/api/logs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                level,
                message,
                timestamp: new Date().toISOString()
            })
        }).catch(() => {
            // fail silently to avoid infinite loop
        });
    } catch (e) {
        // fail silently
    }
}

export function setupLogger() {
    console.log = (...args: any[]) => {
        originalLog(...args);
        sendLogToBackend('log', ...args);
    };

    console.error = (...args: any[]) => {
        originalError(...args);
        sendLogToBackend('error', ...args);
    };

    console.warn = (...args: any[]) => {
        originalWarn(...args);
        sendLogToBackend('warn', ...args);
    };

    console.info = (...args: any[]) => {
        originalInfo(...args);
        sendLogToBackend('info', ...args);
    };

    console.debug = (...args: any[]) => {
        originalDebug(...args);
        sendLogToBackend('debug', ...args);
    };
}
