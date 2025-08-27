[![pytest](https://github.com/ppak10/additive-manufacturing/actions/workflows/pytest.yml/badge.svg)](https://github.com/ppak10/additive-manufacturing/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/github/ppak10/additive-manufacturing/graph/badge.svg?token=O827DEYWQ9)](https://codecov.io/github/ppak10/additive-manufacturing)

# additive-manufacturing
Additive Manufacturing related software modules

## Getting Started
### Installation
```bash
uv add additive-manufacturing
```

### CLI
```bash
am --help
```

### Agent
#### Claude Code
1. Install MCP tools and Agent
- Defaults to claude code
```bash
am mcp install
```
- If updating, you will need to remove the previously existing mcp tools
```bash
claude mcp remove am
```
#### Example
An example implementation can be found [here](https://github.com/ppak10/additive-manufacturing-agent)

