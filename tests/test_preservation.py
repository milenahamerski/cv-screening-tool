from app.preservation_validator import PreservationValidator
from app.optimizer import ResumeOptimizer
from tests.test_helpers import SAMPLE_CV_RAW


def test_preservation_validation():
    struct, opt_text, _ = ResumeOptimizer.optimize(SAMPLE_CV_RAW, "cv.docx")
    check = PreservationValidator.validate_preservation(SAMPLE_CV_RAW, opt_text)

    assert check.is_valid is True
    # Years 2020, 2023, 2018, 2014 must be preserved
    for yr in ["2020", "2023", "2018", "2014"]:
        assert yr in check.preserved_dates

    # No hallucination warnings
    assert not any("Alerta crítico" in w for w in check.hallucination_warnings)


def test_hallucination_detection():
    # If someone tampers with the text and adds Harvard and Google
    tampered_text = SAMPLE_CV_RAW + "\nTrabalhou na Google e fez MBA em Harvard."
    check = PreservationValidator.validate_preservation(SAMPLE_CV_RAW, tampered_text)

    assert check.is_valid is False
    assert any("Google" in w for w in check.hallucination_warnings)
    assert any("Harvard" in w for w in check.hallucination_warnings)
