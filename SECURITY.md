# Security

## Reporting issues

Please use [GitHub **Security** advisories](https://github.com/MatthewEngman/telos-framework/security/advisories/new) (**Report a vulnerability**) for sensitive reports instead of public issues.

## Scope notes

- Telos evaluates MILP objectives and constraints with restricted `eval`. Do not expose the canvas server or untrusted `.telos` files to the internet without additional hardening.
- Never commit API keys or tokens. Use environment variables (e.g. `OPENAI_API_KEY`) and CI secrets only.
