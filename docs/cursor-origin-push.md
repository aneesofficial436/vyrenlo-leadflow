# Push LeadFlow to Cursor (Origin)

Cursor-hosted git (`origin.cursor.com`) is managed with the **`origin` CLI**. On **native Windows**, install **WSL** first — the CLI is supported on macOS, Linux, and WSL only.

## One-time: enable WSL

In **PowerShell (Admin)**:

```powershell
wsl --install
```

Reboot when prompted, then open **Ubuntu** (or your WSL distro) from the Start menu.

## Push from WSL

In the WSL terminal:

```bash
# Install origin CLI
curl -fsSL https://downloads.cursor.com/origin/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Sign in (opens browser)
origin auth login

# Repo on your Windows drive
cd /mnt/c/Users/Convo/vyrenlo-leadflow

# Create Cursor-hosted repo (name must be unique in your namespace)
origin repo create vyrenlo-leadflow

# Add remote (use the HTTPS URL printed by the command above)
git remote add origin <URL_FROM_CREATE_COMMAND>
git push -u origin main
```

After push, open the repository from **Cursor → Codebase** (or the URL printed by `origin repo create`).

## If `repo create` fails

- **No namespace:** team admin sets Origin up at [cursor.com/codebase](https://cursor.com/codebase).
- **Name taken:** try `vyrenlo-leadflow-app` or another variant once.

## Without WSL

Use **GitHub** or another host until Origin supports native Windows, or develop inside a WSL clone of this folder.