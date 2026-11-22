from services.sdr_engine.personalizer import sdr_personalizer

def test_generate_step_1_personalized_email():
    prospect = {
        "first_name": "Elena",
        "company_name": "Brex Cards",
        "title": "Director of Core Systems",
        "tech_stack": ["Elixir", "Kubernetes", "AWS"],
        "recent_signal": "Consolidating travel per diem workflows"
    }
    copy = sdr_personalizer.generate_personalized_email("acme-sales", prospect, step_number=1)
    assert "Elena" in copy["body"]
    assert "Brex Cards" in copy["body"]
    assert "Elixir" in copy["body"]
    assert "Unsubscribe:" in copy["body"]

def test_generate_step_3_breakup_email():
    prospect = {
        "first_name": "Marcus",
        "company_name": "Weights & Biases",
        "title": "VP MLOps",
        "tech_stack": ["PyTorch"],
        "recent_signal": "Launched benchmark suite"
    }
    copy = sdr_personalizer.generate_personalized_email("acme-sales", prospect, step_number=3)
    assert "Closing the loop" in copy["subject"]
    assert "Marcus" in copy["body"]
