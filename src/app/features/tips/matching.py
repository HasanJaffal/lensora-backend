from collections.abc import Sequence

from app.features.tips.models import Tip

MAX_MATCHED_TIPS = 4


def select_matched_tips(
    tips: Sequence[Tip],
    patient_tags: Sequence[str],
    *,
    limit: int = MAX_MATCHED_TIPS,
) -> list[Tip]:
    """Pick the tips whose tags overlap the patient's, most-relevant first (FR-TIP-3).

    Ranked by the number of shared tags so the most relevant guidance surfaces; ties keep
    the catalog order. Pure and deterministic for unit testing.
    """
    wanted = set(patient_tags)
    scored = [
        (len(wanted.intersection(tip.tags)), index, tip)
        for index, tip in enumerate(tips)
    ]
    matches = [entry for entry in scored if entry[0] > 0]
    matches.sort(key=lambda entry: (-entry[0], entry[1]))
    return [tip for _, _, tip in matches[:limit]]
