from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from pathlib import Path
from typing import Iterable, List, Optional

from .config import NewsletterConfig
from .render import html_to_plain


class EmailError(RuntimeError):
    pass


def build_message(
    *,
    sender_email: str,
    sender_name: str,
    recipients: Iterable[str],
    subject: str,
    html_content: str,
    cc: Optional[Iterable[str]] = None,
    bcc: Optional[Iterable[str]] = None,
) -> MIMEMultipart:
    to_list = [item for item in recipients if item]
    if not to_list:
        raise EmailError("No email recipients supplied.")
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = ", ".join(to_list)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg.attach(MIMEText(html_to_plain(html_content), "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    return msg


def _smtp_recipients(msg: MIMEMultipart) -> List[str]:
    values = []
    for header in ["To", "Cc", "Bcc"]:
        if msg.get(header):
            values.extend([item.strip() for item in msg[header].split(",") if item.strip()])
    return values


def send_message(msg: MIMEMultipart) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    if not username or not password:
        raise EmailError("SMTP_USERNAME and SMTP_PASSWORD are required for Gmail SMTP sending.")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as server:
        server.login(username, password)
        refused = server.sendmail(username, _smtp_recipients(msg), msg.as_string())
    if refused:
        raise EmailError(f"SMTP refused recipients: {refused}")


def write_eml(msg: MIMEMultipart, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(msg.as_string(), encoding="utf-8")
    return path


def send_or_draft(
    config: NewsletterConfig,
    *,
    html_path: Path,
    subject: str,
    test: bool = False,
    dry_run: bool = False,
    eml_path: Path = Path("output/scientific-newsletter.eml"),
) -> Path:
    html_content = html_path.read_text(encoding="utf-8")
    email_config = config.email
    recipients = [email_config.get("test_recipient")] if test else list(email_config.get("recipients") or [])
    sender_email = email_config.get("sender_email") or os.environ.get("SMTP_USERNAME", "")
    sender_name = os.environ.get("SMTP_FROM_NAME") or email_config.get("sender_name") or config.name
    msg = build_message(
        sender_email=sender_email,
        sender_name=sender_name,
        recipients=recipients,
        subject=subject,
        html_content=html_content,
    )
    if dry_run or email_config.get("mode") == "draft_only":
        return write_eml(msg, eml_path)
    send_message(msg)
    return html_path
