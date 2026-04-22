# Perplexity MCP Server via Polza.ai

`mcp-name: io.github.ivanantigravity-lgtm/perplexity-polza-mcp-server`

MCP сервер для `Claude Desktop` и `Claude Code`, который ходит в модели Perplexity (`Sonar`, `Sonar Pro`, `Sonar Reasoning`, `Sonar Deep Research`) через агрегатор [Polza.ai](https://polza.ai).

## Что умеет

- `perplexity_model_guide` — шпаргалка по выбору модели под задачу
- `perplexity_ask` — обычный вопрос в Perplexity
- `perplexity_research` — более глубокий ресёрч с веб-поиском
- `list_perplexity_models` — список доступных `perplexity/*` моделей из каталога Polza

## Что нужно для установки

- `Claude Desktop` или `Claude Code` (или любой другой MCP-клиент)
- [`uv`](https://docs.astral.sh/uv/) (ставится одной командой, см. ниже)
- Python 3.11+
- `POLZA_AI_API_KEY` — ключ берётся на [polza.ai/dashboard/api-keys](https://polza.ai/dashboard/api-keys)

Поставить `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Установка за 2 минуты (через PyPI + uvx)

Это самый простой путь: ничего клонировать не надо, `uvx` сам скачает пакет из PyPI.

### Claude Code / VS Code

Создай файл `.mcp.json` в корне своего проекта:

```json
{
  "mcpServers": {
    "perplexity-polza": {
      "command": "uvx",
      "args": ["perplexity-polza-mcp-server@latest"],
      "env": {
        "POLZA_AI_API_KEY": "your-polza-api-key-here"
      }
    }
  }
}
```

Перезапусти Claude Code — готово.

### Claude Desktop (macOS)

Открой файл `~/Library/Application Support/Claude/claude_desktop_config.json` и добавь:

```json
{
  "mcpServers": {
    "perplexity-polza": {
      "command": "uvx",
      "args": ["perplexity-polza-mcp-server@latest"],
      "env": {
        "POLZA_AI_API_KEY": "your-polza-api-key-here"
      }
    }
  }
}
```

Перезапусти Claude Desktop.

### Claude Desktop (Windows)

Файл: `%APPDATA%\Claude\claude_desktop_config.json`. Содержимое такое же, как на macOS.

## Как проверить, что работает

После перезапуска Claude попроси:

> Покажи доступные модели Perplexity через polza

Claude должен вызвать tool `list_perplexity_models` и вернуть список.

## Когда какую модель брать

- `Sonar` — быстрый поиск + ответ. Новости, факты, Q&A, короткие суммаризации.
- `Sonar Pro` — плотнее структура, сравнения, follow-up вопросы.
- `Sonar Pro Search` — глубже поиск, больше поисковых шагов.
- `Sonar Reasoning Pro` — не просто найти, а разобрать и сделать вывод.
- `Sonar Deep Research` — полноценный ресёрч, market scan, длинный отчёт.

Переключить дефолтную модель можно через переменные окружения `PERPLEXITY_MODEL` и `PERPLEXITY_RESEARCH_MODEL` — полный список ниже.

## Переменные окружения

| Переменная | Обязательная | По умолчанию | Описание |
| --- | --- | --- | --- |
| `POLZA_AI_API_KEY` | да | — | Ключ с polza.ai |
| `POLZA_BASE_URL` | нет | `https://polza.ai/api/v1` | Base URL для chat completions (с `/v1` — это ожидаемо, endpoint OpenAI-совместим) |
| `PERPLEXITY_MODEL` | нет | `perplexity/sonar` | Модель для `perplexity_ask` |
| `PERPLEXITY_RESEARCH_MODEL` | нет | `perplexity/sonar-deep-research` | Модель для `perplexity_research` |
| `LOG_LEVEL` | нет | `INFO` | — |

## Локальная разработка

```bash
git clone https://github.com/ivanantigravity-lgtm/perplexity-polza-mcp-server.git
cd perplexity-polza-mcp-server
uv sync
POLZA_AI_API_KEY=your_key uv run python -m perplexity_polza_mcp_server.server
```

Для локального подключения из source в Claude:

```json
{
  "mcpServers": {
    "perplexity-polza-local": {
      "command": "uv",
      "args": ["run", "python", "-m", "perplexity_polza_mcp_server.server"],
      "cwd": "/absolute/path/to/perplexity-polza-mcp-server",
      "env": {
        "POLZA_AI_API_KEY": "your-polza-api-key-here"
      }
    }
  }
}
```

## Под капотом

- Chat completions: `POST https://polza.ai/api/v1/chat/completions` (OpenAI-совместимый формат)
- Model catalog: `GET https://polza.ai/api/v1/models/catalog`

## Важные файлы в репозитории

- `pyproject.toml` — метаданные пакета и entry points
- `server.json` — описание для MCP Registry
- `fastmcp.json` — локальная конфигурация FastMCP
- `.github/workflows/publish-pypi.yml` — публикация в PyPI через GitHub Actions

## Лицензия

MIT.
