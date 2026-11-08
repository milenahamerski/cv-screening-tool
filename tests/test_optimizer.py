from app.optimizer import ResumeOptimizer
from tests.test_helpers import SAMPLE_CV_RAW


def test_optimizer_flow():
    struct, opt_text, steps = ResumeOptimizer.optimize(SAMPLE_CV_RAW, "cv.docx")

    # Step validation
    assert len(steps) >= 6
    assert all(s.status == "completed" for s in steps)

    # Structured resume validation
    assert "João Carlos Pereira" in struct.contact.name or "JOÃO" in opt_text
    assert struct.contact.email == "joao.pereira@email.com"
    assert "TechSolutions Corp" in opt_text
    assert "InovaWeb Softwares" in opt_text

    # Check that passive voice was polished
    assert "Desenvolveu" in opt_text or "desenvolveu" in opt_text.lower()
    assert "Responsável por desenvolver" not in opt_text

    # Check skills preserved and consolidated
    assert "Python" in struct.skills or "Python" in opt_text
    assert "SQL" in struct.skills or "SQL" in opt_text


def test_no_hallucinations_in_optimizer():
    # If the user CV does not mention a prestigious company like Google or Netflix, optimizer must not add it
    _, opt_text, _ = ResumeOptimizer.optimize(SAMPLE_CV_RAW, "cv.docx")
    assert "Google" not in opt_text
    assert "Harvard" not in opt_text
    assert "Netflix" not in opt_text
