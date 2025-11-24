export function consumeSSE(
    url: string,
    onMessage: (data: any) => void,
    options?: { signal?: AbortSignal }
) {
    const eventSource = new EventSource(url);

    if (options?.signal) {
        options.signal.addEventListener('abort', () => {
            eventSource.close();
        });
    }

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            onMessage(data);
        } catch (e) {
            console.error('Failed to parse SSE message', e);
        }
    };

    eventSource.onerror = (err) => {
        console.error('SSE error', err);
        eventSource.close();
    };

    return eventSource;
}
