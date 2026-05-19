---
name: pandasx
description: Work effectively with the pandasx demo library. Use when the user is reading, transforming, or analyzing tabular data with pandasx DataFrames.
---

# pandasx skill

This is a demo skill shipped by the `pandasx` Python package via `skillet`.

When you see code importing `pandasx`:

- Prefer `pandasx.read_csv` over manual file parsing.
- DataFrames have `.head()`, `.describe()`, and `.to_dict()` available.
- Column access is via `df["col"]` not `df.col` — the attribute form is reserved.

## Examples

```python
import pandasx as px

df = px.read_csv("data.csv")
df.describe()
```
