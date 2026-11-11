# Asset-owned language metadata

Assets keep canonical Name/Category/Tags as identity and filter keys. Optional
`localizations` stores display names, category labels, tag-key/label maps and
randomization explanations for each language. Schema-1 libraries and packages
remain readable. Chinese and English are the initially required translations;
the dictionary can hold additional languages without renaming the asset.

Language changes only read saved fields. They never launch AI, change appearance
revisions, rewrite existing canonical text, rebind Rhino materials or alter Latin
plant identity. PlantNames reads valid asset language labels first, then the older
PlantIdentity.Names dictionary, then the authored/scientific-name fallback.

Each translated name/category/recommendation records its exact source. A source
edit makes only that translated field stale; display falls back to the source
until it is completed again. Tag translations are keyed by original tags, so
selection/filter keys and IDs do not change. Search includes valid saved labels
from all languages, preserving an English search when switching to Chinese.

New material labeling and verified plant resolution request zh/en fields in the
structured AI answer. Missing/misaligned language output is rejected. Existing
image-import recovery still retains a generated image if classification fails;
those assets explicitly need metadata completion. Portable asset ZIPs include
language metadata automatically.

Both library-management sections offer **Complete asset translations**. The same
operations are exposed through the original Platform API:

- `material_catalog_localize`: metadata-only completion for missing/stale fields.
- `plant_catalog_localize`: same operation for the plant library.
- Both return `{job: ...}` or `{job:null}` if complete; poll/cancel with the existing
  `material_catalog_status` / `material_catalog_cancel` operations.

The runner has no tools, image generation or executable actions. Batches are
collected before one library-locked, journalled commit. Every source ID, appearance
revision and catalog revision is checked, and canonical fields must match exactly.
Valid existing translations are preserved. A concurrent edit rejects the whole
commit; cancellation before commit makes no library changes. Completion increments
CatalogRevision only; images, dimensions, Revision and taxonomy stay unchanged.

Native captions and tooltips use UiCaption ownership. Editable source fields
remain authored data; tooltips and contextual instruction suffixes are localized
independently of those values. No periodic text translation is used.

Validation: `--asset-languages` exercises stale fallback, search/filter identity,
no-op completion, conflict/partial-commit rejection, ZIP roundtrip and plant
identity. `--asset-labels-ai` is an explicit metadata-only real-runner smoke test;
it is excluded from ordinary builds. The B regression also checks source fields,
image hashes and revision policy across actual completion and language switching.
