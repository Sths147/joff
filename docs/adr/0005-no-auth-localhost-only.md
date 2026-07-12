# No authentication; web app is bound to localhost only

The app holds PISTE and Mistral credentials server-side and triggers external API calls that
consume quota/cost money. Rather than adding auth, it's deliberately scoped to run on
localhost or a home network only, not exposed on the public internet — revisit if remote
access is ever wanted.
