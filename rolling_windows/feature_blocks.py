from __future__ import annotations

BANK_FEATS_DIM = 60

BANK_FEATS_BLOCKS: dict[str, list[int]] = {
    "state_feats": [45, 54, 55, 56, 57, 58, 59],
    "legal_feats": [1, 9, 14, 15, 16, 17, 18, 19, 21, 22, 27, 41],
    "governance_feats": [3, 4, 5, 6, 10, 33, 34, 38, 40, 42, 44, 46],
    "finance_feats": [8, 12, 23, 28, 32, 36, 39, 47],
    "ip_feats": [25, 31, 37, 48],
    "ops_feats": [20, 43, 49, 50, 51, 52, 53],
}


def other_bank_feats_indices() -> list[int]:
    used: set[int] = set()
    for indices in BANK_FEATS_BLOCKS.values():
        used.update(indices)

    return [i for i in range(BANK_FEATS_DIM) if i not in used]

