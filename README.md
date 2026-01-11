[![claude-code](https://github.com/ppak10/workspace-agent/actions/workflows/claude-code.yml/badge.svg)](https://github.com/ppak10/workspace-agent/actions/workflows/claude-code.yml)
[![gemini-cli](https://github.com/ppak10/workspace-agent/actions/workflows/gemini-cli.yml/badge.svg)](https://github.com/ppak10/workspace-agent/actions/workflows/gemini-cli.yml)
[![codex](https://github.com/ppak10/workspace-agent/actions/workflows/codex.yml/badge.svg)](https://github.com/ppak10/workspace-agent/actions/workflows/codex.yml)
[![pytest](https://github.com/ppak10/additive-manufacturing/actions/workflows/pytest.yml/badge.svg)](https://github.com/ppak10/additive-manufacturing/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/github/ppak10/additive-manufacturing/graph/badge.svg?token=O827DEYWQ9)](https://codecov.io/github/ppak10/additive-manufacturing)

# additive-manufacturing

Additive Manufacturing related software modules
<p align="center">
  <img src="./icon.svg" alt="Logo" width="50%">
</p>

## Getting Started
### Installation

```bash
uv add additive-manufacturing
```

### Agent
#### Claude Code

1. Install MCP tools and Agent

- Defaults to claude code
```bash
am mcp install
```

#### Claude Desktop

1. Install MCP tools (Development)

```bash
am mcp install claude-desktop --project-path /path/to/additive-manufacturing
```

Note: After installation, restart Claude Desktop for the changes to take effect.

### CLI (`am --help`)
#### 1. Create Workspace (via `workspace-agent`)
```bash
am workspace create test
```

#### Example
An example implementation can be found [here](https://github.com/ppak10/additive-manufacturing-agent)
