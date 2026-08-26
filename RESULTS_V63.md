# v0.63 — pre-seal source-contract qualification

## Purpose

v0.63 adds a prospective `Q0_SOURCE_CONTRACT_QUALIFICATION` stage before a future fresh source/change request may be sealed. It addresses a process failure exposed twice by the project: a binary can be authentic while its semantic schema disagrees with the registration/documentation, and discovering that only after opening the evidence stage wastes a fresh evidence opportunity.

Q0 is **not validation**. It does not inspect row, outcome, exposure or feature values; fit models; calculate performance; or create committee-gate credit. It authenticates a pinned binary and text documentation, then inspects only object/column-name metadata.

## Metadata reader boundary

The intended API is `pyreadr.list_objects()`, not `pyreadr.read_r()`. During implementation, both pyreadr 0.5.3 and current 0.5.6 failed on the historical RDA files because `ListObjectsParser` lacks the row-name callback expected by librdata. The v0.63 executor applies one narrowly scoped compatibility patch: a no-op `handle_row_name(name, index)` method. The callback immediately discards row names; it does not add a column-value/text-value callback and does not store, compare or persist row names.

The workflow statically forbids `pyreadr.read_r()` in the qualifier/executor and keeps temporary RDA binaries under `/tmp`, outside the Git worktree.

## Retrospective replay on already-consumed sources

No new fresh source was opened. Q0 was replayed only on sources already consumed by historical incidents.

### pg15training / historical MCR-XGB-MOTOR-002 S1

Pinned identity:

- CASdatasets commit `227fb56b8734bdb7c0327a41180e01d2ddaeaf26`;
- `data/pg15training.rda`;
- 1,934,161 bytes;
- Git blob `9e670d214c05a7454d558ab32de5df96a6b0aba6`;
- pinned documentation `man-md/pg15training.md`, Git blob `9c0f44bd6bc2b24c760917398c6c0783b916d1f5`.

The proposed/registered semantic schema contained `Expdays`; binary metadata contained `Exppdays`. The Levenshtein distance is 1. Q0 returns:

`SOURCE_CONTRACT_QUALIFICATION_BLOCK_BEFORE_SEAL`

No alias is applied automatically. Had Q0 existed prospectively, this typo/documentation-vs-binary conflict could have been resolved before sealing a fresh evidence request rather than consuming S1.

### euMTPL / historical v0.57–v0.58

Pinned identity:

- same CASdatasets commit;
- `data/euMTPL.rda`;
- 17,829,164 bytes;
- Git blob `4bb386d89606eb5b529206d0835e11074103042b`;
- pinned documentation `man-md/euMTPL.md`, Git blob `c50e96b2a4a470edb000fd71de0f2f01334799c7`.

The registered/documented schema contained `cost_fcd` / `num_fcd`; binary metadata contained `cost_fcg` / `num_fcg`. Both registered-to-binary near matches have Levenshtein distance 1. Q0 again returns:

`SOURCE_CONTRACT_QUALIFICATION_BLOCK_BEFORE_SEAL`

## Prospective rule

For future fresh evidence work, Q0 must pass **before** a source stage/request is sealed. It may authenticate the pinned binary and use schema-only metadata inspection. A missing/extra semantic identifier, near match or documentation-vs-binary conflict blocks sealing for explicit review. Near matches never auto-correct the registration.

A source blocked at Q0 has not generated model-performance evidence and has not consumed a sealed evidence stage because no row/outcome value was inspected. Once Q0 passes and a future request is sealed, the existing stricter post-access fail-closed rules still apply.

## Historical boundary

v0.63 is prospective process control only. It does not reopen or repair euMTPL v0.58, MCR-XGB-MOTOR-001 or terminal `MCR-XGB-MOTOR-002`; it does not authorise S2/S3 under MCR-002 and does not create MCR-003.

The historical state remains **5/8**, `HOLD / HOLD_SHADOW_ONLY / NOT_OPEN`, with customer pricing unauthorised.
