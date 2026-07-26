from enum import StrEnum


class AttachmentFolder(StrEnum):
    """The closed set of subfolders an attachment may be stored under.

    Clients send one of these values; arbitrary folder names are rejected at the boundary so a
    request can never place an object outside its organization's known layout.
    """

    PATIENT_DOCUMENTS = "patient-documents"
    PATIENT_IMAGES = "patient-images"
    REPORTS = "reports"
