from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Iterable

from ..config import get_settings
from ..repo.mysql import mail_log_repo, positions_repo, signals_repo


class MailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def render_daily_mail(self, session) -> str:
        positions = await positions_repo.get_current_positions(session)
        signals = await signals_repo.list_recent(session, limit=10)
        html_positions = "".join(
            f"<tr><td>{p.code}</td><td>{p.weight:.2%}</td><td>{p.market_value:.2f}</td></tr>"
            for p in positions
        )
        html_signals = "".join(
            f"<tr><td>{s.code}</td><td>{s.side}</td><td>{s.qty}</td><td>{s.price}</td></tr>"
            for s in signals
        )
        html = f"""
        <h2>Daily Signal Summary</h2>
        <h3>Signals</h3>
        <table>{html_signals or '<tr><td colspan="4">No signals</td></tr>'}</table>
        <h3>Positions</h3>
        <table>{html_positions or '<tr><td colspan="3">No positions</td></tr>'}</table>
        """
        return html

    async def send_mail(self, session, html: str, recipients: Iterable[str]) -> None:
        settings = self.settings
        subject = "Daily Trading Report"
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.smtp_user
        message["To"] = ",".join(recipients)
        message.attach(MIMEText(html, "html", "utf-8"))
        ok = True
        error = None
        if settings.env.lower() == "prod":
            try:
                with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
                    smtp.login(settings.smtp_user, settings.smtp_pass)
                    smtp.sendmail(settings.smtp_user, list(recipients), message.as_string())
            except Exception as exc:  # noqa: BLE001
                ok = False
                error = str(exc)
        await mail_log_repo.log_mail(session, subject, recipients, ok, error)
        if not ok:
            raise RuntimeError(f"Failed to send mail: {error}")


__all__ = ["MailService"]
