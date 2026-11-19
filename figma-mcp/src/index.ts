#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { FigmaClient, parseFileKey, parseNodeId } from "./figma.js";

const token = process.env.FIGMA_API_KEY ?? process.env.FIGMA_TOKEN;
if (!token) {
  console.error("Ошибка: задайте переменную окружения FIGMA_API_KEY (Figma Personal Access Token).");
  process.exit(1);
}

const figma = new FigmaClient(token);
const server = new McpServer({ name: "figma-mcp", version: "0.1.0" });

const MAX_CHARS = 100_000;

type ToolResult = { content: { type: "text"; text: string }[]; isError?: boolean };

function ok(data: unknown): ToolResult {
  let text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  if (text.length > MAX_CHARS) {
    text =
      text.slice(0, MAX_CHARS) +
      `\n\n...[обрезано, ${text.length - MAX_CHARS} символов. Уменьшите depth или запросите конкретные node_ids]`;
  }
  return { content: [{ type: "text", text }] };
}

async function run(fn: () => Promise<unknown>): Promise<ToolResult> {
  try {
    return ok(await fn());
  } catch (e) {
    return { content: [{ type: "text", text: (e as Error).message }], isError: true };
  }
}

const fileArg = z.string().describe("Ключ файла Figma или полный URL файла");

server.tool(
  "get_file",
  "Получить структуру файла Figma (страницы и дерево нод). Используйте depth, чтобы ограничить размер ответа.",
  {
    file: fileArg,
    depth: z.number().int().min(1).max(10).default(2).describe("Глубина дерева (по умолчанию 2)"),
    version: z.string().optional().describe("ID версии файла"),
  },
  ({ file, depth, version }) =>
    run(() => figma.get(`/files/${parseFileKey(file)}`, { depth, version })),
);

server.tool(
  "get_nodes",
  "Получить конкретные ноды файла по ID (формат '1:2') или по URL с node-id.",
  {
    file: fileArg,
    node_ids: z.array(z.string()).min(1).describe("Список ID нод, например ['1:2']"),
    depth: z.number().int().min(1).max(10).optional().describe("Глубина поддерева"),
  },
  ({ file, node_ids, depth }) =>
    run(() =>
      figma.get(`/files/${parseFileKey(file)}/nodes`, {
        ids: node_ids.map(parseNodeId).join(","),
        depth,
      }),
    ),
);

server.tool(
  "get_images",
  "Получить ссылки на рендер нод в виде изображений (png, jpg, svg, pdf).",
  {
    file: fileArg,
    node_ids: z.array(z.string()).min(1),
    format: z.enum(["png", "jpg", "svg", "pdf"]).default("png"),
    scale: z.number().min(0.01).max(4).default(1).describe("Масштаб (0.01–4)"),
  },
  ({ file, node_ids, format, scale }) =>
    run(() =>
      figma.get(`/images/${parseFileKey(file)}`, {
        ids: node_ids.map(parseNodeId).join(","),
        format,
        scale,
      }),
    ),
);

server.tool(
  "get_image_fills",
  "Получить ссылки на все изображения, использованные как заливки в файле.",
  { file: fileArg },
  ({ file }) => run(() => figma.get(`/files/${parseFileKey(file)}/images`)),
);

server.tool(
  "get_comments",
  "Получить комментарии к файлу.",
  { file: fileArg },
  ({ file }) => run(() => figma.get(`/files/${parseFileKey(file)}/comments`)),
);

server.tool(
  "get_file_components",
  "Список компонентов файла (библиотеки).",
  { file: fileArg },
  ({ file }) => run(() => figma.get(`/files/${parseFileKey(file)}/components`)),
);

server.tool(
  "get_file_styles",
  "Список стилей файла (цвета, текст, эффекты, сетки).",
  { file: fileArg },
  ({ file }) => run(() => figma.get(`/files/${parseFileKey(file)}/styles`)),
);

server.tool(
  "get_file_variables",
  "Локальные переменные (design tokens) файла. Требует Enterprise-план и scope file_variables:read.",
  { file: fileArg },
  ({ file }) => run(() => figma.get(`/files/${parseFileKey(file)}/variables/local`)),
);

server.tool(
  "get_file_versions",
  "История версий файла.",
  { file: fileArg },
  ({ file }) => run(() => figma.get(`/files/${parseFileKey(file)}/versions`)),
);

server.tool(
  "get_team_projects",
  "Список проектов команды.",
  { team_id: z.string() },
  ({ team_id }) => run(() => figma.get(`/teams/${team_id}/projects`)),
);

server.tool(
  "get_project_files",
  "Список файлов проекта.",
  { project_id: z.string() },
  ({ project_id }) => run(() => figma.get(`/projects/${project_id}/files`)),
);

server.tool("get_me", "Информация о текущем пользователе (проверка токена).", {}, () =>
  run(() => figma.get("/me")),
);

await server.connect(new StdioServerTransport());
console.error("figma-mcp запущен (stdio)");
