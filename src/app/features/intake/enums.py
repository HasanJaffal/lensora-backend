from enum import StrEnum


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class VisualProblem(StrEnum):
    BLURRED_VISION = "blurredVision"
    COLOUR_VISION = "colourVision"
    DOUBLE_VISION = "doubleVision"
    FIXATION_CONCENTRATION = "fixationConcentration"
    VISUAL_FIELD = "visualField"
    PHORIA = "phoria"
    TROPIA = "tropia"


class FunctionalSign(StrEnum):
    PHOTOPHOBIA = "photophobia"
    TEARING = "tearing"
    REDNESS = "redness"
    VERTIGO = "vertigo"
    BLEPHAROSPASM = "blepharospasm"
    FLOATERS = "floaters"
    PHOSPHENES = "phosphenes"
    HALOS = "halos"
    HEADACHE = "headache"
    OCULAR_PAIN = "ocularPain"
    BURNING = "burning"
    ITCHING = "itching"
    DRYNESS = "dryness"
    DISCHARGE = "discharge"
    SWELLING = "swelling"
    FOREIGN_BODY_SENSATION = "foreignBodySensation"
    NIGHT_BLINDNESS = "nightBlindness"
    EYE_STRAIN = "eyeStrain"


class Onset(StrEnum):
    SUDDEN = "sudden"
    PROGRESSIVE = "progressive"


class CorrectionPreference(StrEnum):
    EYEGLASSES = "eyeglasses"
    CONTACTS = "contacts"
    NO_PREFERENCE = "noPreference"
