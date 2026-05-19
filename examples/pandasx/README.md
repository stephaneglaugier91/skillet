# pandasx (demo)

A throwaway package that demonstrates shipping a Claude Code skill via `skillet`.

```bash
pip install -e .
# Now users can do either of these:
skillet install pandasx --local
pandasx-skillet install --local
```

The skill files live in `src/pandasx/skills/pandasx/` and are advertised via the
`[project.entry-points."skillet.skills"]` table in `pyproject.toml`.
