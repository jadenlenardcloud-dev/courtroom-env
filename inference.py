[project]
name = "courtroom-argument-simulator"
version = "1.0.0"
description = "OpenEnv-compliant courtroom argument simulator for RL agent training"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0.0",
    "openai>=1.0.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["."]
