# Perplexity MCP Server via Polza.ai

`mcp-name: io.github.ivanantigravity-lgtm/perplexity-polza-mcp-server`

MCP сервер для `Claude Desktop`, который ходит в модели Perplexity через `Polza.ai`.

Сделан в формате Python/FastMCP, чтобы его можно было нормально публиковать в:

- GitHub
- PyPI
- MCP Registry

## Что умеет

- `perplexity_model_guide` — шпаргалка по выбору модели под задачу
- `perplexity_ask` — обычный вопрос в Perplexity
- `perplexity_research` — более глубокий ресерч с веб-поиском
- `list_perplexity_models` — список доступных `perplexity/*` моделей из каталога Polza

## Когда какую модель брать

`Sonar`

Быстрый поиск + ответ. Хорош для новостей, фактов, Q&A, коротких суммаризаций и быстрых “что сейчас происходит”.

`Sonar Pro`

Когда обычный `Sonar` уже мелковат. Лучше для сравнений, более плотной структуры и follow-up вопросов.

`Sonar Pro Search`

Когда нужен более глубокий поиск, больше поисковых шагов и более агрессивный сбор источников.

`Sonar Reasoning Pro`

Когда важнее не просто найти, а аккуратно разобрать, сравнить и сделать вывод.

`Sonar Deep Research`

Когда задача уже похожа на полноценный ресерч, market scan или длинный отчёт по теме.

## Локальный запуск

Нужен Python 3.11+ и `uv`.

```bash
uv run python -m perplexity_polza_mcp_server.server
```

## Переменные окружения

```env
POLZA_API_KEY=your_polza_api_key
POLZA_BASE_URL=https://polza.ai/api/v1
PERPLEXITY_MODEL=perplexity/sonar
PERPLEXITY_RESEARCH_MODEL=perplexity/sonar-deep-research
LOG_LEVEL=INFO
```

## Конфиг Claude Desktop

Файл на macOS:

`~/Library/Application Support/Claude/claude_desktop_config.json`

Пример:

```json
{
  "mcpServers": {
    "perplexity-polza": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "-m",
        "perplexity_polza_mcp_server.server"
      ],
      "cwd": "/Users/ivankhokholkov/perplexity-mcp-polza",
      "env": {
        "POLZA_API_KEY": "YOUR_POLZA_API_KEY",
        "POLZA_BASE_URL": "https://polza.ai/api/v1",
        "PERPLEXITY_MODEL": "perplexity/sonar",
        "PERPLEXITY_RESEARCH_MODEL": "perplexity/sonar-deep-research",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Публикация

Собрать пакет:

```bash
uv run python -m build
```

Проверить пакет:

```bash
uv run python -m twine check dist/*
```

PyPI workflow уже лежит в `.github/workflows/publish-pypi.yml`.

Для MCP Registry подготовлен файл `server.json`.

## Важные файлы

- `pyproject.toml` — метаданные пакета и entry points
- `server.json` — описание для MCP Registry
- `fastmcp.json` — локальная конфигурация FastMCP
- `.github/workflows/publish-pypi.yml` — публикация в PyPI через GitHub Actions

## По API

- Chat completions: `POST https://polza.ai/api/v1/chat/completions`
- Model catalog: `GET https://polza.ai/api/v1/models/catalog`
