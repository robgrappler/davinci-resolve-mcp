# Scripts

Phase 3 collapsed this directory from a forest of launcher wrappers down to
two installers and two preflight checks. The MCP server itself is no longer
launched via a wrapper — it runs as `python -m davinci_resolve_mcp` (or the
`davinci-resolve-mcp` console script installed by the package), invoked
directly by your MCP client.

## Installers

`setup/install.sh` (macOS/Linux) and `setup/install.bat` (Windows) create a
virtualenv next to the project, install the package in editable mode, and
print next-step guidance for configuring an MCP client.

```bash
./scripts/setup/install.sh
```

```batch
scripts\setup\install.bat
```

## Preflight check

`check-resolve-ready.sh` and `check-resolve-ready.bat` verify that
DaVinci Resolve is running, the `RESOLVE_SCRIPT_API` / `RESOLVE_SCRIPT_LIB`
environment variables resolve to real paths, and the `davinci_resolve_mcp`
package is importable. Run this whenever the server is misbehaving — it
does **not** start the server.

```bash
./scripts/check-resolve-ready.sh
```

```batch
scripts\check-resolve-ready.bat
```

## Launching the server

After installation, configure your MCP client to launch:

```
python -m davinci_resolve_mcp
```

Configuration templates live under `config/`. See `INSTALL.md` for the
end-to-end setup.
