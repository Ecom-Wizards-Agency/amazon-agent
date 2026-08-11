# Amazon Ads OAuth callback

This Worker provides the secure browser handoff for the Ecom Wizards Amazon
Ads OAuth grant. It never receives the LWA client secret and never exchanges or
stores authorization codes, access tokens, or refresh tokens.

Production endpoints:

- `GET https://auth.ecomwizards.agency/health`
- `GET https://auth.ecomwizards.agency/amazon/start`
- `GET https://auth.ecomwizards.agency/amazon/callback`

The callback signs a 15-minute OAuth state, binds it to a secure browser cookie,
validates both on return, and displays the short-lived code for immediate local
exchange with `../exchange_token.py`.

## Local verification

```bash
npm install
npx wrangler types
npm run check
npm test
npm run dry-run
```

For local development only, place a strong `STATE_SIGNING_KEY` in an ignored
`.dev.vars` file. Never commit that file.

## Production deployment

The production Worker requires the `STATE_SIGNING_KEY` Cloudflare secret before
deployment. `wrangler.jsonc` declares it as required, disables `workers.dev` and
preview URLs, disables invocation URL logs, and attaches the Custom Domain.

The exact Allowed Return URL in the LWA Web Settings must be:

`https://auth.ecomwizards.agency/amazon/callback`

## Amazon prerequisite

This callback does not grant Amazon Ads API scopes. The Amazon Ads developer
overview must show `advertising::campaign_management` on this LWA client before
the authorization page can succeed. If the overview still says the app has no
Ads API scopes, stop there and complete Amazon's API-access assignment first.
