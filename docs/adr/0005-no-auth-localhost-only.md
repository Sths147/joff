# No authentication; web app is bound to localhost only

> **Superseded by [ADR 0007](0007-multi-user-auth.md)**: the app moved from a localhost-only
> personal tool to a publicly reachable, multi-user server, which is exactly the "remote access"
> case this ADR flagged as the trigger to revisit.

The app holds PISTE and Mistral credentials server-side and triggers external API calls that
consume quota/cost money. Rather than adding auth, it's deliberately scoped to run on
localhost or a home network only, not exposed on the public internet — revisit if remote
access is ever wanted.
