---
description: Create and manage knowledge bases with tags, ACLs, and hierarchical organization for scoped RAG
argument-hint: [create|list|tag|acl|tags|node-tags] [--visibility private|shared]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Knowledge Base Management

Create scoped knowledge bases for RAG, manage tags and access control.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `create` (default), `list`, `tag`, `acl`, `tags`, `node-tags`
- **--visibility**: Pre-select visibility level

## Endpoint Map (sub-resources)

| Resource | Endpoint | Operations |
|----------|----------|------------|
| tags | `/api/v1/kb-tags` | list, create, update, delete |
| node-tags | `/api/v1/node-tags` | list, create, delete |

## Route by Action

### List

```bash
curl -s "${RAILYARD_URL}/api/v1/knowledge-bases?limit=50" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, visibility, is_system, tags, created_at}'
```

### Create (default)

Interview:

1. **"What should this knowledge base be called?"** (name)

2. **"Description?"** (optional)

3. **"Visibility?"**
   - private — Only you can access (default)
   - shared — Other users can access via ACLs

4. **"Is this a child of an existing knowledge base?"**
   - If yes: list existing KBs, ask which parent
   - If no: top-level KB

5. **"Any tags to apply?"**
   - List existing tags: `GET /api/v1/kb-tags`
   - User picks existing tags and/or names new ones

Execute:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/knowledge-bases" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"...","description":"...","visibility":"private","parent_kb_id":"uuid or null"}'
```

If new tags requested, create them first:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/kb-tags" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"...","color":"#hex"}'
```

Then assign tags:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/knowledge-bases/${KB_ID}/tags" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"tag_id":"uuid"}'
```

### Tag

Manage KB tags.

Interview:

1. **"Create a new tag or list existing?"**
   - list: `GET /api/v1/kb-tags`
   - create: ask for name, description, color

### Tags (kb-tags CRUD)

Full CRUD on `/api/v1/kb-tags`.

Interview for create:
- **name** (required)
- **color** (hex, e.g. `#3366ff`)
- **scope** (`global` | `kb` | `node`)

```bash
# List
curl -s "${RAILYARD_URL}/api/v1/kb-tags?limit=50" \
  -H "Authorization: Bearer ${TOKEN}"

# Create
curl -s -X POST "${RAILYARD_URL}/api/v1/kb-tags" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"...","color":"#3366ff","scope":"kb"}'

# Update
curl -s -X PUT "${RAILYARD_URL}/api/v1/kb-tags/${TAG_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"...","color":"#...","scope":"..."}'

# Delete
curl -s -X DELETE "${RAILYARD_URL}/api/v1/kb-tags/${TAG_ID}" \
  -H "Authorization: Bearer ${TOKEN}"
```

### Node-Tags

List, create, delete on `/api/v1/node-tags` (no update — recreate to change).

Interview for create:
- **node_id** (required — KB node UUID)
- **tag_id** (required — kb-tag UUID)
- **applied_by** (`user` | `automation`)

```bash
# List
curl -s "${RAILYARD_URL}/api/v1/node-tags?node_id=${NODE_ID}" \
  -H "Authorization: Bearer ${TOKEN}"

# Create
curl -s -X POST "${RAILYARD_URL}/api/v1/node-tags" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"node_id":"...","tag_id":"...","applied_by":"user"}'

# Delete
curl -s -X DELETE "${RAILYARD_URL}/api/v1/node-tags/${NODE_TAG_ID}" \
  -H "Authorization: Bearer ${TOKEN}"
```

### ACL

Manage access control on a knowledge base.

Interview:

1. List KBs: `GET /api/v1/knowledge-bases?limit=50`
2. **"Which knowledge base?"**
3. **"Action?"**
   - list — Show current ACLs: `GET /api/v1/knowledge-bases/{id}/acls`
   - grant — Add access: ask for user/group ID, permission level
   - revoke — Remove access: list ACLs, ask which to remove

## Report

Show the output to the user.
