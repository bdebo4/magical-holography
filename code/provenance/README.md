# Provenance records

These files are documentation, not runtime inputs -- nothing under `code/src` or `code/tests`
reads them. They record where the code in this capsule came from, for a reviewer who wants to
trace a specific function or design decision back to its origin.

- `source_repositories.json` -- the two private research repositories this capsule's
  circuit-construction and analysis code was refactored from, and one credential file that was
  found and deliberately excluded rather than staged.
- `notebook_cells.csv` -- one row per audited source notebook cell: a stable ID (e.g.
  `WH16-C-C039`), the source notebook name, the cell's 1-based index, a content hash, and a short
  description of its role. Modules and configs elsewhere in `code/` cite these IDs (e.g. "source
  cell WH16-C-C039") as a citation, the same way a paper cites a section number -- it identifies
  where the logic came from without implying the reviewer needs access to the original notebook.
