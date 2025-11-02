# Managing Neon API Keys

Most actions performed in the Neon Console can also be performed via the Neon API. To authenticate API calls, you need an API key. Each key is a randomly generated 64-bit token that remains valid until it is explicitly revoked.

## Types of API Keys

| Key Type | Who Can Create | Scope | Validity |
| --- | --- | --- | --- |
| Personal API Key | Any user | All organization projects where the user is a member | Valid until revoked; organization project access ends if the user leaves the organization |
| Organization API Key | Organization administrators | All projects within the organization | Valid until revoked |
| Project-scoped API Key | Any organization member | Single specified project | Valid until revoked or when the project leaves the organization |

There is no strict limit to the number of API keys you can create, though Neon recommends staying below 10,000 keys per account.

## Creating API Keys

You must create your first personal API key in the Neon Console. Afterward, you can use that key to create additional keys via the API.

> **Note**
> When you create an API key in the Neon Console, the secret token is displayed only once. Copy and store it immediately in a secure credential manager (e.g., AWS Key Management Service or Azure Key Vault). If a key is lost, revoke it and create a replacement.

### Create a Personal API Key

You can generate a personal API key in the console or using the API (once you already have at least one personal key).

```bash
curl https://console.neon.tech/api/v2/api_keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PERSONAL_API_KEY" \
  -d '{"key_name": "my-key"}'
```

**Request body parameters**

- `key_name`: A descriptive name for the API key (for example, `development`, `staging`, or `ci-pipeline`).

**Example response**

```json
{
  "id": 177630,
  "key": "neon_api_key_1234567890abcdef1234567890abcdef"
}
```

### Create an Organization API Key

Organization API keys provide administrator-level access to all resources in an organization. Only organization administrators can create these keys. Use a personal API key that belongs to an administrator to create an organization key.

```bash
curl --request POST \
     --url 'https://console.neon.tech/api/v2/organizations/{org_id}/api_keys' \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer $PERSONAL_API_KEY' \
     --data '{"key_name": "orgkey"}'
```

**Example response**

```json
{
  "id": 165434,
  "key": "neon_org_key_1234567890abcdef1234567890abcdef",
  "name": "orgkey",
  "created_at": "2022-11-15T20:13:35Z",
  "created_by": "user_01h84bfr2npa81rn8h8jzz8mx4"
}
```

### Create a Project-Scoped API Key

Project-scoped keys grant member-level access to a single project. They cannot delete the project, cannot access organization-level functionality, and stop working if the project is transferred out of the organization.

Any organization member can create a project-scoped key for an organization-owned project:

```bash
curl --request POST \
     --url 'https://console.neon.tech/api/v2/organizations/{org_id}/api_keys' \
     --header 'Content-Type: application/json' \
     --header 'Authorization: Bearer $PERSONAL_API_KEY' \
     --data '{"key_name":"only-this-project", "project_id": "some-project-123"}'
```

**Request body parameters**

- `org_id`: The ID of the organization.
- `key_name`: A descriptive name for the API key.
- `project_id`: The ID of the project that the API key can access.

**Example response**

```json
{
  "id": 1904821,
  "key": "neon_project_key_1234567890abcdef1234567890abcdef",
  "name": "test-project-scope",
  "created_at": "2024-12-11T21:34:58Z",
  "created_by": "user_01h84bfr2npa81rn8h8jzz8mx4",
  "project_id": "project-id-123"
}
```

## Using an API Key

The following example shows how to use an API key to retrieve projects:

```bash
curl 'https://console.neon.tech/api/v2/projects' \
  -H 'Accept: application/json' \
  -H "Authorization: Bearer $NEON_API_KEY" | jq
```

- `https://console.neon.tech/api/v2/projects` is the Neon API endpoint.
- `Accept: application/json` requests a JSON response.
- `Authorization: Bearer $NEON_API_KEY` supplies the API key in the request header. Replace `$NEON_API_KEY` with an actual 64-bit Neon API key. Requests missing this header, or using an invalid or revoked key, receive a `401 Unauthorized` response.
- `jq` is optional but useful for pretty-printing the JSON response.

## Listing API Keys

To list personal API keys:

```bash
curl "https://console.neon.tech/api/v2/api_keys" \
  -H "Authorization: Bearer $NEON_API_KEY" \
  -H "Accept: application/json" | jq
```

To list organization API keys:

```bash
curl "https://console.neon.tech/api/v2/organizations/{org_id}/api_keys" \
  -H "Authorization: Bearer $NEON_API_KEY" \
  -H "Accept: application/json" | jq
```

## Revoking API Keys

Revoke keys that are no longer needed or that may have been compromised. Revocation is immediate and permanent. Subsequent requests using a revoked key fail with `401 Unauthorized`, and a revoked key cannot be reactivated.

- Personal API keys can only be revoked by their owners.
- Organization API keys can be revoked by organization administrators.
- Project-scoped keys can be revoked by organization administrators.

Use the following API method to revoke a key by its `key_id`:

```bash
curl -X DELETE \
  'https://console.neon.tech/api/v2/api_keys/177630' \
  -H "Accept: application/json"  \
  -H "Authorization: Bearer $NEON_API_KEY" | jq
```

## Additional Resources

- [Neon API reference](https://api-docs.neon.tech/)
- [Neon Discord server](https://discord.gg/neondatabase)

_Last updated: September 5, 2025_
