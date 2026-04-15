# Asyngram Telegram bot framework

A lightweight, asynchronous Python framework for building Telegram bots. Designed for simplicity, readability, and production use.

## Installation

```bash
pip install asyngram
```

## Quick Start

```python
from asyngram import Bot, bold

bot = Bot("YOUR_BOT_TOKEN")

@bot.on.message.command("start")
async def start(ctx):
    await ctx.answer(f"Hello, {bold(ctx.user.first_name)}!")

bot.run()
```

## How It Works

Asyngram uses a context-based approach. Every handler receives a `ctx` object that gives you access to:
- Message data (`ctx.text`, `ctx.user`, `ctx.message`)
- Response methods (`ctx.answer()`, `ctx.reply()`, `ctx.edit()`, `ctx.notify()`)
- State management (`ctx.state.set()`, `ctx.state.get_data()`, `ctx.state.finish()`)

Routing is handled via decorators. Handlers are evaluated top-to-bottom, and the first matching handler executes.

## Key Features

- **Async/Await:** Non-blocking architecture built on `aiohttp`.
- **FSM (State Machine):** Manage multi-step flows like registrations or surveys. Data is automatically scoped per user/chat.
- **Middleware Pipeline:** Built-in logging, throttling, and error handling. Easy to extend with custom middleware.
- **Keyboard Builders:** Create Reply and Inline keyboards with method chaining. No manual JSON formatting.
- **Smart Responses:** `ctx.answer()` automatically decides whether to send a new message or edit the existing one.
- **Formatting Helpers:** Clean functions like `bold()`, `italic()`, `code()`, and `link()`.

## Documentation

Full guides, API reference, and troubleshooting are available at:
[docs.asyngram.dev](https://docs.asyngram.dev)

## Included Examples

Four ready-to-run examples are provided in the repository:
1. `echobot.py` - Commands, text routing, and fallback handling
2. `registration_bot.py` - FSM step flow with validation and keyboards
3. `inline_menu_bot.py` - Callback parsing, prefix routing, and dynamic edits
4. `production_bot.py` - Environment config, custom middleware, logging, and shutdown handling

Run any example after installing the package and replacing the bot token.

## Recommended Project Layout

Asyngram 100% asynchronous telegram bot framework from Mosa Atabek Sadullah

Author:
Firstname: Mosa(Musabek)
Father's Name: Atabek(Otabek)
Surname: Sadullah(Sadulla)
