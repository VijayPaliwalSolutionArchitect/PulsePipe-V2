from evals.run_evals import run_evals_gate

def test_evals_gate_release_criteria():
    assert run_evals_gate() is True
