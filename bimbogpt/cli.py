"""
CLI for BiMBoGPT.

Usage:
    bimbogpt --help
    bimbogpt --register none|code|agent|mcp
    bimbogpt "summarize this in 1 word: <content>"
"""

import sys
import click
from typing import Optional

from .register import register, PLATFORMS


@click.group(invoke_without_command=True)
@click.option("--register", "platform", type=click.Choice(PLATFORMS + ["help"]),
              help="Register BiMBoGPT with a platform")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.pass_context
def main(ctx: click.Context, platform: Optional[str], verbose: bool) -> None:
    """BiMBoGPT - Babble In Means Better Out.
    
    Drop-in OpenAI wrapper that injects babble priming for better reasoning.
    
    \b
    Quick usage:
        from bimbogpt import BimboClient
        client = BimboClient()
        response = client.chat.completions.create(...)
    """
    if platform:
        register(platform, verbose=verbose)
        return
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("text", required=False)
@click.option("--mode", type=click.Choice(["word", "sentence", "paragraph"]),
              default="word", help="Output mode")
@click.option("--model", default="gpt-4", help="Model to use")
@click.option("-f", "--fifo", is_flag=True, help="Use FIFO agent delegation")
def process(text: Optional[str], mode: str, model: str, fifo: bool) -> None:
    """Process text with babble priming.
    
    Reads from stdin if no text provided.
    """
    if text is None:
        if sys.stdin.isatty():
            click.echo("Error: Provide text or pipe input", err=True)
            sys.exit(1)
        text = sys.stdin.read()
    
    # Build the prompt
    prompt = f"Answer this in 1 {mode}: {text}"
    messages = [{"role": "user", "content": prompt}]
    
    if fifo:
        from .fifo import delegate_to_agent
        response = delegate_to_agent(messages, model=model)
        click.echo(response)
    else:
        from .client import BimboClient
        client = BimboClient(verbose=True)
        response = client.chat.completions.create(model=model, messages=messages)
        click.echo(response.choices[0].message.content)


@main.command()
def init() -> None:
    """Initialize config file at ~/.bimbogpt/config.toml."""
    from .config import Config
    path = Config.init_config()
    click.echo(f"Created config file: {path}")
    click.echo("Edit this file to tune babble settings.")


@main.command()
@click.argument("text", required=False)
def strip(text: Optional[str]) -> None:
    """Strip babble from text.
    
    Pipe LLM responses through this to remove babble prefix.
    
    Example:
        echo "blah blah blah... The answer is Paris" | bimbogpt strip
    """
    from .stripper import strip_babble
    
    if text is None:
        if sys.stdin.isatty():
            click.echo("Error: Provide text or pipe input", err=True)
            sys.exit(1)
        text = sys.stdin.read()
    
    click.echo(strip_babble(text))


if __name__ == "__main__":
    main()
