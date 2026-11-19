const BASE_URL = "https://api.figma.com/v1";

export class FigmaClient {
  constructor(private token: string) {}

  async get<T = unknown>(
    path: string,
    params: Record<string, string | number | undefined> = {},
  ): Promise<T> {
    const url = new URL(BASE_URL + path);
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
    }
    const res = await fetch(url, { headers: { "X-Figma-Token": this.token } });
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      throw new Error(`Figma API ${res.status} ${res.statusText}: ${body}`);
    }
    return (await res.json()) as T;
  }
}

/** Принимает ключ файла или полный URL Figma и возвращает ключ файла. */
export function parseFileKey(input: string): string {
  const m = input.match(/figma\.com\/(?:file|design|board|proto)\/([A-Za-z0-9]+)/);
  return m ? m[1] : input.trim();
}

/** URL вида ...?node-id=1-2 -> "1:2". */
export function parseNodeId(input: string): string {
  const m = input.match(/node-id=([^&#]+)/);
  const raw = m ? decodeURIComponent(m[1]) : input;
  return raw.replace(/-/g, ":");
}
