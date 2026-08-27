"""Email notifications via Gmail SMTP (STARTTLS)."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .models import Listing


def send_email(cfg: dict, subject: str, body: str) -> None:
    """cfg is the [email] config section."""
    msg = EmailMessage()
    msg["From"] = cfg["username"]
    msg["To"] = cfg["to"]
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"]), timeout=30) as s:
        s.starttls()
        s.login(cfg["username"], cfg["app_password"])
        s.send_message(msg)


def match_email(listing: Listing, prefilled: bool) -> tuple[str, str]:
    """Build (subject, body) for a matched listing."""
    subject = f"🏠 {listing.summary()}"

    lines = [
        listing.title,
        "",
        f"Rooms:   {listing.rooms:g}" if listing.rooms is not None else "",
        f"Size:    {listing.area:g} m²" if listing.area is not None else "",
        f"Rent:    {listing.rent_gross:.2f} € warm"
        + (f"  ({listing.rent_net:.2f} € kalt)" if listing.rent_net else "")
        if listing.rent_gross is not None else "",
        f"Address: {listing.address}",
        f"Free from: {listing.occupation_date}" if listing.occupation_date else "",
        f"WBS:     {'required' if listing.wbs_required else 'not required'}",
        f"Company: {listing.company_name}",
        "",
        f"Listing: {listing.deeplink}",
        "",
    ]
    if prefilled:
        lines += [
            "✅ The application form has been pre-filled and left OPEN in your browser.",
            "   Review the details and click the submit button (Anfrage versenden / Absenden).",
        ]
    else:
        lines += [
            "ℹ️ No auto-fill adapter for this company — open the listing above and apply manually.",
        ]
    body = "\n".join(l for l in lines if l is not None)
    return subject, body


if __name__ == "__main__":
    # Smoke test: send a test email using config.toml.
    from .config import load

    cfg = load()
    send_email(
        cfg["email"],
        "HomeFinder test email",
        "If you can read this, SMTP is configured correctly.",
    )
    print("Test email sent to", cfg["email"]["to"])
