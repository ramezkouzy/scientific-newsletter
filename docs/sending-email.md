# Sending Email

Scientific Newsletter supports two modes.

## Draft-Only Mode

Use this first.

```yaml
email:
  mode: "draft_only"
```

Then run:

```bash
scientific-newsletter send --test --dry-run
```

The command writes `output/scientific-newsletter.eml`. Open it in an email client or inspect it as text. It is a proper `multipart/alternative` message with plaintext first and HTML second.

## Gmail SMTP Mode

Use Gmail SMTP only after a successful draft.

1. Enable two-factor authentication on your Google account.
2. Create an app password at https://myaccount.google.com/apppasswords.
3. Add credentials to `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=your.name@gmail.com
SMTP_PASSWORD=your_16_character_app_password
SMTP_FROM_NAME=Scientific Newsletter
```

4. Set the config mode:

```yaml
email:
  mode: "gmail_smtp"
```

5. Send to yourself first:

```bash
scientific-newsletter send --test
```

6. Send to the configured recipient list only after review:

```bash
scientific-newsletter send
```

## Recipient List

In `config/newsletter.yaml`:

```yaml
email:
  recipients:
    - colleague@example.com
    - fellow@example.com
```

Keep the test recipient separate:

```yaml
email:
  test_recipient: "you@example.com"
```

## Common Failures

- `SMTP_USERNAME and SMTP_PASSWORD are required`: `.env` is missing credentials.
- Gmail rejects login: create a new app password and confirm two-factor authentication is enabled.
- Email displays as markup: use this sender, which sends both plaintext and HTML parts.
- Links look wrong: rerun `scientific-newsletter render`; the quality gate checks that prose links came from prepared papers.
