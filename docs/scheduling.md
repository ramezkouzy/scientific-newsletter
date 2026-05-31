# Scheduling

The setup wizard asks how often the newsletter should run and stores the result in `config/newsletter.yaml`.

Example:

```yaml
schedule:
  frequency: "twice_weekly"
  weekdays: ["Tuesday", "Friday"]
  time: "06:00"
```

## Print The Schedule

```bash
scientific-newsletter schedule
```

This prints the cron block without installing it.

## Install Locally

```bash
scientific-newsletter schedule --yes
```

The installed job runs:

```bash
scientific-newsletter run --dry-run
```

That means scheduled runs create a preview and prompt, but do not send email automatically. This is the safer default for clinical and scientific communication.

## Change The Schedule

Edit `config/newsletter.yaml`, then reinstall:

```bash
scientific-newsletter schedule --yes
```

The crontab block is wrapped in markers:

```text
# scientific-newsletter start
# scientific-newsletter end
```

Reinstalling replaces the old block.
