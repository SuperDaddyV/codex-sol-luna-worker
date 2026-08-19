# ModelDial fixture attribution

`api-complete.json` is derived from ModelDial Public Radar batch
`snapshot-2026-08-13T00-00-00Z`, published at `2026-08-13T00:00:00Z` and
retrieved on 2026-08-13 from:

https://modeldial.com/api/v1/radar/latest.json

The fixture is modified and truncated for offline tests. Five Luna score and
reference-cost rows retain the public schema shape. Five sanitized Sol rows were
derived solely to exercise same-batch, same-pricing, same-effort comparison, and
`batch.entryCount` was adjusted to 10. The publisher-defined batch SHA is
retained as fixture data; it is not a hash of this modified file.

`first-party-complete.json` is a wholly sanitized companion fixture derived from
the documented full-snapshot field shape. Its identifiers, scores, reference
costs, and evidence group are synthetic and contain no private or live payload.

Source data license: Creative Commons Attribution 4.0 International (CC BY 4.0).

https://modeldial.com/data-license

The repository source code remains licensed separately under the project MIT
license.
