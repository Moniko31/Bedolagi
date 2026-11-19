# figma-mcp

MCP-сервер (stdio) для чтения данных Figma через REST API.

## Установка

```bash
npm install
npm run build
```

## Токен

Figma → Settings → Security → Personal access tokens. Нужны scopes: `file_content:read`, `file_comments:read`, `library_content:read`, `projects:read`, `current_user:read` (и `file_variables:read` для переменных, Enterprise).

## Подключение к Claude Code

```bash
claude mcp add figma -e FIGMA_API_KEY=figd_xxx -- node /root/projects/figma-mcp/build/index.js
```

Или в `.mcp.json`:

```json
{
  "mcpServers": {
    "figma": {
      "command": "node",
      "args": ["/root/projects/figma-mcp/build/index.js"],
      "env": { "FIGMA_API_KEY": "figd_xxx" }
    }
  }
}
```

## Инструменты

`get_file`, `get_nodes`, `get_images`, `get_image_fills`, `get_comments`, `get_file_components`, `get_file_styles`, `get_file_variables`, `get_file_versions`, `get_team_projects`, `get_project_files`, `get_me`.

Везде, где нужен файл, можно передавать ключ или полный URL; ID нод принимаются в формате `1:2` или `1-2`.
