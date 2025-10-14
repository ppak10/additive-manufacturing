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

- If updating, you will need to remove the previously existing MCP tools
```bash
claude mcp remove am
```

### CLI (`am --help`)
#### 1. Create Workspace (via `workspace-agent`)
```bash
wa workspace init test
```

#### Example
An example implementation can be found [here](https://github.com/ppak10/additive-manufacturing-agent)
