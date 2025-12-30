const API_BASE = 'http://localhost:8000';

export interface SetVaultRequest {
  thread_id: string;
  vault_path: string;
}

export interface SetVaultResponse {
  status: string;
  message: string;
  thread_id: string;
}

export interface ChatRequest {
  message: string;
  thread_id?: string;
}

export interface ChatResponse {
  response: string;
  thread_id: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  async setVault(request: SetVaultRequest): Promise<SetVaultResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/set-vault`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `API error: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Unknown error');
    }
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `API error: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Unknown error');
    }
  }

  async *chatStream(request: ChatRequest): AsyncGenerator<string, string, unknown> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      let finalThreadId = request.thread_id || '';
      let currentEvent = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
            continue;
          }

          if (line.startsWith('data:')) {
            const data = line.slice(5).trim();

            if (currentEvent === 'token') {
              try {
                // The data is JSON-encoded, so parse it
                const token = JSON.parse(data);
                yield token;
              } catch (e) {
                console.error('Failed to parse token:', data);
              }
            } else if (currentEvent === 'done') {
              finalThreadId = data;
            }

            currentEvent = ''; // Reset event type
          }
        }
      }

      return finalThreadId;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Unknown error');
    }
  }
}

export const api = new ApiClient();
