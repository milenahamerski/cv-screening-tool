from app.analyzer import ResumeAnalyzer
from tests.test_helpers import SAMPLE_CV_RAW


def test_analyzer_objective_scoring():
    diag = ResumeAnalyzer.analyze(SAMPLE_CV_RAW, "curriculo.docx")

    assert 0 <= diag.overall_score <= 100
    assert len(diag.criteria) == 6
    criterion_ids = [c.criterion_id for c in diag.criteria]
    assert "structure" in criterion_ids
    assert "impact" in criterion_ids
    assert "action_verbs" in criterion_ids
    assert "keywords" in criterion_ids
    assert "readability" in criterion_ids
    assert "contact" in criterion_ids

    # Scores must match sum of criteria
    expected_sum = int(round(sum(c.score for c in diag.criteria)))
    assert diag.overall_score == expected_sum

    # Must provide key issues and positive points
    assert len(diag.positive_points) > 0
    assert diag.has_extractable_text is True


def test_analyzer_consistency():
    # Analyzing identical text twice must yield strictly identical results
    diag1 = ResumeAnalyzer.analyze(SAMPLE_CV_RAW, "cv.pdf")
    diag2 = ResumeAnalyzer.analyze(SAMPLE_CV_RAW, "cv.pdf")

    assert diag1.overall_score == diag2.overall_score
    for c1, c2 in zip(diag1.criteria, diag2.criteria):
        assert c1.score == c2.score
        assert c1.criterion_id == c2.criterion_id


def test_empty_text_analysis():
    empty_diag = ResumeAnalyzer.analyze("", "vazio.pdf")
    assert empty_diag.overall_score == 0
    assert empty_diag.has_extractable_text is False


SAMPLE_ENGLISH_CV = """# JOHN DOE
john.doe@example.com | +1 (555) 019-2834 | linkedin.com/in/johndoe | github.com/johndoe | New York, NY

## PROFESSIONAL SUMMARY
Senior Backend Software Engineer with 6+ years of experience designing scalable distributed systems, microservices, and high-throughput REST APIs using Python, Go, and PostgreSQL. Proven track record of improving system reliability and reducing infrastructure costs.

## WORK EXPERIENCE

**ACME CLOUD SOLUTIONS**
**Senior Software Engineer | March 2022 – Present**
- Architected and deployed microservices architecture handling over 10M daily requests with 99.99% uptime.
- Reduced API latency by 45% through Redis caching and query optimization in PostgreSQL.
- Spearheaded database migration saving $120,000 annually in AWS cloud infrastructure expenses.
- Led an agile team of 5 engineers conducting code reviews and CI/CD automation with GitHub Actions and Docker.

**GLOBAL TECH CORP**
**Software Developer | June 2019 – February 2022**
- Engineered customer notification pipeline using Apache Kafka and FastAPI, processing 500,000 events daily.
- Automated end-to-end integration test suites with Pytest, increasing test coverage from 60% to 92%.
- Collaborated with product managers to deliver 12 core product features ahead of schedule.

## EDUCATION

**CORNELL UNIVERSITY**
Bachelor of Science in Computer Science | 2015 – 2019
GPA: 3.8 / 4.0

## SKILLS & TECHNOLOGIES
**Languages:** Python, Go, SQL, TypeScript, Java
**Frameworks & Tools:** FastAPI, Django, Docker, Kubernetes, AWS, PostgreSQL, Redis, Kafka
**Practices:** CI/CD, Microservices, REST APIs, Agile, Automated Testing
"""


def test_analyzer_english_resume_scoring():
    diag = ResumeAnalyzer.analyze(SAMPLE_ENGLISH_CV, "john_doe_resume.pdf")

    assert diag.language == "en"
    assert diag.overall_score >= 80

    # Ensure English action verbs and metrics were recognized
    crit_map = {c.criterion_id: c for c in diag.criteria}
    assert crit_map["action_verbs"].score >= 12  # Out of 15
    assert crit_map["impact"].score >= 15        # Out of 20
    assert crit_map["structure"].score >= 18     # Out of 20
    assert crit_map["keywords"].score >= 12      # Out of 15
    assert crit_map["contact"].score == 15       # Full contact score

    # Check that feedback messages are provided in Portuguese even for English CV
    assert any("verbos de ação" in pos.lower() for pos in diag.positive_points)
    assert any("métricas" in pos.lower() or "quantificados" in pos.lower() for pos in diag.positive_points)

