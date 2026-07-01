"""Async mailbox for vault-owner <-> BONSAI communication.

Messages are stored as JSONL lines in .mailbox.jsonl at the vault root.
Each line: {"id", "ts", "from", "to", "body", "read", "context"}.
Participants are free-form strings; common names are "owner" and "bonsai".
"""

import json
import uuid
from datetime import datetime, timezone

import click

from bonsai import VAULT_ROOT

MAILBOX_PATH = VAULT_ROOT / ".mailbox.jsonl"


def _load_messages() -> list[dict]:
    if not MAILBOX_PATH.exists():
        return []
    messages = []
    for line in MAILBOX_PATH.read_text().splitlines():
        line = line.strip()
        if line:
            messages.append(json.loads(line))
    return messages


def _save_messages(messages: list[dict]) -> None:
    with MAILBOX_PATH.open("w") as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")


def _append_message(msg: dict) -> None:
    with MAILBOX_PATH.open("a") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")


def _format_message(msg: dict, short: bool = False) -> str:
    status = " " if msg.get("read") else "*"
    ts = msg["ts"][:16].replace("T", " ")
    header = f"[{status}] {msg['id'][:8]}  {ts}  {msg['from']} -> {msg['to']}"
    if short:
        body_preview = msg["body"][:80].replace("\n", " ")
        return f"{header}  {body_preview}"
    parts = [header]
    if msg.get("context"):
        parts.append(f"    context: {msg['context']}")
    parts.append(f"    {msg['body']}")
    return "\n".join(parts)


@click.group()
def mailbox():
    """Async mailbox for vault-owner <-> BONSAI communication."""


@mailbox.command()
@click.argument("body")
@click.option("--from", "sender", required=True, help="Who is sending the message.")
@click.option("--to", "recipient", required=True, help="Who should receive the message.")
@click.option("--context", default=None, help="Optional task or ref context.")
def send(body: str, sender: str, recipient: str, context: str | None) -> None:
    """Send a message."""
    msg = {
        "id": uuid.uuid4().hex,
        "ts": datetime.now(timezone.utc).isoformat(),
        "from": sender,
        "to": recipient,
        "body": body,
        "read": False,
        "context": context,
    }
    _append_message(msg)
    click.echo(f"Sent {msg['id'][:8]} ({sender} -> {recipient})")


@mailbox.command()
@click.option("--for", "recipient", default="bonsai", help="Show unread messages for this recipient.")
def unread(recipient: str) -> None:
    """Show unread messages."""
    messages = _load_messages()
    unread_msgs = [m for m in messages if m["to"] == recipient and not m.get("read")]
    if not unread_msgs:
        click.echo(f"No unread messages for {recipient}.")
        return
    click.echo(f"{len(unread_msgs)} unread message(s) for {recipient}:\n")
    for msg in unread_msgs:
        click.echo(_format_message(msg))
        click.echo()


@mailbox.command("list")
@click.option("--from", "sender", default=None)
@click.option("--to", "recipient", default=None)
@click.option("-n", "limit", type=int, default=20, help="Max messages to show.")
@click.option("--short", is_flag=True, help="One-line format.")
def list_messages(sender: str | None, recipient: str | None, limit: int, short: bool) -> None:
    """List messages, newest first."""
    messages = _load_messages()
    if sender:
        messages = [m for m in messages if m["from"] == sender]
    if recipient:
        messages = [m for m in messages if m["to"] == recipient]
    messages = messages[-limit:]
    if not messages:
        click.echo("No messages.")
        return
    for msg in reversed(messages):
        click.echo(_format_message(msg, short=short))
        if not short:
            click.echo()


@mailbox.command()
@click.argument("message_ids", nargs=-1, required=True)
def read(message_ids: tuple[str, ...]) -> None:
    """Mark message(s) as read by ID prefix."""
    messages = _load_messages()
    marked = 0
    for msg in messages:
        for prefix in message_ids:
            if msg["id"].startswith(prefix) and not msg.get("read"):
                msg["read"] = True
                marked += 1
    _save_messages(messages)
    click.echo(f"Marked {marked} message(s) as read.")


@mailbox.command()
@click.option("--for", "recipient", default="bonsai")
def count(recipient: str) -> None:
    """Count unread messages."""
    messages = _load_messages()
    n = sum(1 for m in messages if m["to"] == recipient and not m.get("read"))
    click.echo(str(n))
