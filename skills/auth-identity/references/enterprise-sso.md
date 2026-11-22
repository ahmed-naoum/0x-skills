# Enterprise SSO and provisioning

Read this when: a business customer asks for SAML or OIDC single sign-on, SCIM or directory
sync, group-to-role mapping or SSO enforcement, or an SSO connection fails against a customer's
Okta, Entra ID or Google Workspace.

## Build or buy

| Option | Fits | Cost |
|---|---|---|
| A managed provider's enterprise SSO (WorkOS, Clerk, Auth0, Stytch and similar) | The first enterprise deals; no time to learn each identity provider | A fee per connection or a higher tier, passed on in enterprise pricing |
| An open-source bridge that presents every SAML or OIDC connection to the app as one OIDC provider (Ory Polis, formerly BoxyHQ SAML Jackson; Keycloak as a broker) | Many connections, cost pressure, or a self-hosted product | One more service to run and patch |
| The auth library's SSO plugin | The library already owns auth and offers one | The plugin's maturity; the customer setup screen is still to build |
| A SAML library used directly (`@node-saml/node-saml` and similar) | Nothing above fits | Every validation rule below becomes the project's own responsibility |

Default: buy or bridge for the first connections. The protocol is the small part. The real work
is per-provider setup guides, a self-serve admin screen, certificate rotation, SCIM, a test
matrix and support calls with customers' IT staff. Revisit when per-connection fees dominate.

Never implement XML signature validation or SAML parsing by hand, and patch SAML dependencies
within days of an advisory. Signature-wrapping and parser-differential bugs keep recurring in
widely used SAML libraries, and each one is an authentication bypass for every customer.

Whether SSO is reserved for an enterprise tier is a pricing decision: `0x:pricing-monetization`.

## SAML and OIDC connections

Offer both. Many IT teams default to SAML; OIDC is simpler and safer where the customer's
identity provider (IdP) supports it for custom apps.

Keep one `sso_connections` row per customer connection: organization, type, status (draft,
tested, active), the IdP's entity ID or issuer, sign-on URL, signing certificates (plural, for
rotation), OIDC client ID and encrypted secret, verified domains, default role, and the JIT and
enforcement flags. Each connection has its own ACS URL (`/sso/saml/<connection id>/acs`) and
service-provider entity ID, so the tenant is known from the URL before anything in the message
is trusted.

Validation the SAML library must be configured to perform:

| Check | Stops |
|---|---|
| A signature over the assertion, or a response signature that covers it, verified with the certificate stored for this connection and never the one embedded in the message | Forged assertions |
| Claims read from the same signed element that was verified | Signature wrapping |
| `Issuer` equals the connection's entity ID; `Audience` equals this service provider's entity ID; `Destination` and `Recipient` equal this ACS URL | Assertions meant for another app or connection |
| `NotBefore` and `NotOnOrAfter`, with a few minutes of skew | Old assertions |
| `InResponseTo` matches a request this app issued; assertion IDs cached until expiry and refused a second time | Replay and injection |
| The user's email domain is one of the connection's verified domains | An admin of customer A asserting `ceo@customer-b.com` |

The last row is the multi-tenant rule that matters most. An SSO login lands only in the
organization that owns the connection, and only for identities in that organization's verified
domains or provisioned by it.

- **Identity key:** connection ID plus a persistent NameID or immutable ID attribute (Okta's user
  ID, Entra's object ID). Not the email: people are renamed and addresses are reassigned. Email
  arrives as an attribute.
- **IdP-initiated login** (the tile in the IdP dashboard) sends an unsolicited response with
  nothing tying it to a request, which makes it injectable. Keep it off by default. Offer a
  bookmark tile that points to the SP-initiated start URL (`/sso/start?connection=<id>`), or
  discard the unsolicited response and start an SP-initiated flow for that connection.
- `RelayState` is untrusted input: relative return paths only.
- The ACS endpoint receives a cross-site POST. Exempt it from the CSRF origin check, do not rely
  on `SameSite=Lax` cookies there, and keep issued request IDs on the server.
- Certificates expire. Store the expiry, warn the customer's admin 30 and 7 days ahead, accept
  two certificates during rotation, and prefer a metadata URL refreshed on a schedule over pasted
  XML.
- Skip single logout: it is unreliable across IdPs. Bound the SSO session (8 to 24 hours) and
  rely on SCIM deprovisioning.
- OIDC connections: the customer supplies issuer, client ID and secret. Run the standard code
  flow with discovery and the validations in `oauth-oidc.md`, with `iss` pinned per connection.
- The setup screen shows the ACS URL and entity ID, ingests metadata, maps attributes, and has a
  "test connection" step that must pass before activation.

## Routing users by verified domain

Login is email-first: the user enters an address, the app looks up the domain, and either
redirects to that organization's IdP with `login_hint` or shows the normal methods.

- A domain routes only after the organization proves control with a DNS TXT record holding a
  random value, checked by the app and rechecked periodically because domains lapse and change
  hands. Without proof any customer could claim `bigco.com` and capture BigCo's sign-ins.
- Refuse public mail domains (gmail.com, outlook.com and the like). One domain belongs to one
  organization; a second claim goes to support.
- A verified domain unlocks separate switches, each off by default: SSO routing, SSO
  enforcement, automatic joining for new signups, and capture of existing personal accounts on
  the domain (those users choose between becoming managed and changing their email).
- Every other sign-in path honors enforcement: password, magic link, social login, passkey and
  password reset. "Sign in with Google" on an enforced domain redirects to the IdP like the rest.
- Revealing that a domain uses SSO is acceptable, since it is organization-level information.
  Revealing whether a specific user exists is not.
- Guests: a contractor at `agency.com` invited into BigCo's organization is outside BigCo's
  domain. Make it an organization setting: guests sign in their own way with MFA (the default),
  or membership only through the IdP.
- A user in several organizations re-authenticates through the right IdP when entering an
  enforced one. The session records which connection authenticated it and the guard compares.

## SCIM provisioning

SSO alone creates and updates users at login. It does nothing when an employee is removed: their
session and API tokens live on. SCIM lets the customer's directory push create, update and
deactivate, and deprovisioning is the feature the customer is buying.

SCIM 2.0 is RFC 7643 and RFC 7644. The IdP is the client. The app serves `/Users`, `/Groups`,
`/ServiceProviderConfig`, `/Schemas` and `/ResourceTypes` under one base URL. Authentication is a
long-lived bearer token per organization: generated in the admin screen, shown once, stored
hashed, rotatable, and scoped so that no request can read or change another organization's users.

| Operation | What arrives | Handle as |
|---|---|---|
| Existence check before create | `GET /Users?filter=userName eq "a@b.com"` | Support `eq` on `userName` and `externalId`. Not found is 200 with `totalResults: 0`, not 404 |
| Create | `POST /Users` | 201 with the app's `id`; store `externalId`; 409 on conflict |
| Deactivate | `PATCH` setting `active` to false; Okta and Entra both send this rather than DELETE | Suspend the membership and revoke sessions, refresh tokens and API tokens at once |
| Reactivate | `PATCH` setting `active` to true | Restore the membership |
| Delete | `DELETE /Users/<id>`; Entra sends it some time after deactivation | Remove the membership; keep the organization's data |
| Group change | `PATCH /Groups/<id>` adding or removing members | Recompute roles from the mapping |

- Parse liberally. Entra capitalizes operation names (`"Replace"`), may send `active` as the
  string `"False"`, and uses path filters such as `emails[type eq "work"].value`. Okta mixes PUT
  and PATCH.
- Pagination uses `startIndex`, which is 1-based, and `count`. Errors use the SCIM error schema
  with a `status` field.
- Entra provisions on a fixed cycle of tens of minutes, so deactivation is not instant. Okta
  pushes within seconds to minutes.
- Deprovisioning removes access to that organization. It does not delete the global user, who
  may belong elsewhere, and it leaves organization data in place.
- SCIM-managed users cannot edit their name or email in the app. An email change arriving by
  SCIM is accepted when the new address is in the verified domains.
- With SCIM on, offer "only provisioned users may sign in", which turns JIT off.
- Deprovisioning a sole owner must not orphan the organization (`account-recovery.md`).
- Google Workspace provisions automatically only to apps in its catalog. For those customers rely
  on JIT with short sessions, or on a vendor's directory sync.
- A vendor's directory sync delivers the same events as webhooks: verify signatures and process
  idempotently (`0x:api-design`).

## Group mapping and just-in-time provisioning

- JIT: the first successful SSO login creates the user and a membership with the connection's
  default role, which is the least privileged one.
- Role mapping is data that the customer's admin edits: connection plus IdP group identifier maps
  to a role. Never infer a role from a group's name, and never accept an IdP attribute for
  anything outside that organization.
- Groups arrive as a SAML attribute or OIDC claim at login, or through SCIM group push.
  Login-time claims change roles only at the user's next sign-in; SCIM changes them when the
  directory changes. Prefer SCIM where the customer has it.
- Entra sends group object IDs, not names, and for users in many groups (over 150 for SAML, 200
  for JWT) omits the claim and points to its Graph API instead. Ask the customer to emit only
  the groups assigned to the application.
- Several matching groups: take the highest role, and document that. No match: the default role
  or a denial, as the organization chooses.
- With mapping on, the IdP is the source of truth. Disable manual role edits for SSO-managed
  users, or the next login silently reverts them.
- Guard two invariants in code: mapping never removes the last owner, and never grants
  product-staff or cross-organization privileges.

## Enforcement and break-glass

The product enforces the activation order: configure the connection, pass "test connection",
have the configuring admin complete one real SSO login, verify the domain, and only then allow
"require SSO". Enforcement switched on before a successful login locks out the whole
organization.

When enforcement turns on, password, social and magic-link sign-in stop for members, password
reset is disabled for them, and existing non-SSO sessions are revoked or expire within hours.
Personal API tokens keep working until the member is deprovisioned; say so in the UI.

Break-glass exists because IdPs go down, certificates expire and admins misconfigure:

- Organization owners keep a non-SSO sign-in with mandatory MFA. Each use is logged and notifies
  all owners.
- Alternatively, one-time bypass codes are generated when enforcement is enabled and stored by
  the customer.
- A support procedure with identity verification can disable enforcement (`account-recovery.md`).
- Break-glass never extends to ordinary members and never skips MFA.

## Testing against real identity providers

Get developer tenants: Okta offers a free developer organization, Entra ID comes with any Azure
account, and Google needs a Workspace or Cloud Identity account. In CI use a mock SAML IdP
container and a mock OIDC issuer. Run the real IdPs by hand before each release that touches SSO.

| IdP | Setup | Quirks |
|---|---|---|
| Okta | Custom SAML app: "Single sign-on URL" is the ACS URL and "Audience URI" is the entity ID; add attribute statements and a group attribute filter | SCIM needs provisioning enabled on the app integration; deactivation arrives as `active: false` |
| Entra ID | Enterprise application, non-gallery: "Identifier" is the entity ID and "Reply URL" is the ACS URL | The default NameID is the user principal name, which may not be a mailbox: map email from `user.mail` and expect it empty for some accounts. Groups are GUIDs. Use "Provision on demand" instead of waiting for the cycle |
| Google Workspace | Custom SAML app with ACS URL and entity ID; NameID defaults to the primary email | No SCIM for custom apps; directory changes can take hours to apply |

Matrix per IdP: SP-initiated login; first login (JIT) and second login (update); a user not
assigned to the app is refused; a group change changes the role; an email renamed in the IdP
keeps the same account; SCIM create, update, deactivate (sessions die) and reactivate;
certificate rotation with two certificates live.

Security negatives, automated against the mock IdP, all of which must fail: an unsigned
assertion; an assertion signed by another certificate; a valid assertion from connection A
posted to connection B's ACS URL; a replayed assertion; an expired assertion; a wrong audience;
an email outside the verified domains; a NameID containing an XML comment.

Debugging: capture the SAML response with a browser SAML tracer extension in a test tenant. In
production, log the assertion ID, issuer, connection and failing check, not the assertion body.
Give customers' admins plain errors ("the audience configured in your identity provider does not
match").

## Ask the user

- **How many customers will need SSO in the next year, and what do they pay?** It decides buying
  per connection against running a bridge. Default: buy or bridge until fees dominate.
- **Is SSO a paid enterprise feature or available to everyone?** It is a revenue lever and a
  recurring complaint from security-minded buyers. Default: enterprise tier, with MFA free for
  all.
- **May organizations that enforce SSO still have outside guests?** Agencies and contractors
  depend on it. Default: guests allowed with their own sign-in and mandatory MFA, switchable per
  organization.
- **When a directory deactivates someone, what happens to their work?** Default: the membership is
  suspended, all tokens are revoked, and the data stays with the organization.
- **Who can break glass for a locked-out customer, and on what proof?** Default: organization
  owners with MFA; otherwise support, only after the verification steps in `account-recovery.md`.
