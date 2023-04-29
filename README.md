# Site Claim

## Installation install from pypi or git

- Install the app and pre-reqs

```
    pip install allianceauth-site-claim

or

    pip install git+https://github.com/Solar-Helix-Independent-Transport/allianceauth-site-claim.git
```

- add `'siteclaim',`
  and `'solo',` ( if its not already there )
  to your local.py
- migrate
- restart auth and authbot

## Settings

| Setting                   | Default | What it does                    |
| ------------------------- | ------- | ------------------------------- |
| `SITE_CLAIM_ENABLE_SITES` | True    | Enable or disable the Sites Cog |
| `SITE_CLAIM_ENABLE_ESS`   | True    | Enable or disable the ESS Cog   |
