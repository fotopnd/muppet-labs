from error_hide_seek.scoring.scorer import is_true_positive, score_detections


def test_is_true_positive_excerpt_in_planted():
    assert is_true_positive(
        "neural networks improve safety", "neural networks improve safety metrics"
    )


def test_is_true_positive_planted_in_excerpt():
    assert is_true_positive(
        "we show that neural networks improve safety overall", "neural networks improve safety"
    )


def test_is_true_positive_case_insensitive():
    assert is_true_positive(
        "Neural Networks Improve Safety", "neural networks improve safety metrics"
    )


def test_is_true_positive_false():
    assert not is_true_positive(
        "completely unrelated text excerpt here", "neural networks improve safety"
    )


def test_is_true_positive_strips_whitespace():
    assert is_true_positive(
        "  neural networks improve safety  ", "neural networks improve safety metrics"
    )


def test_score_detections_one_tp():
    planted_detected, fp_count = score_detections(
        ["neural networks improve safety", "unrelated claim here at all"],
        "neural networks improve safety metrics",
    )
    assert planted_detected is True
    assert fp_count == 1


def test_score_detections_no_tp():
    planted_detected, fp_count = score_detections(
        ["unrelated text one", "unrelated text two"],
        "neural networks improve safety metrics",
    )
    assert planted_detected is False
    assert fp_count == 2


def test_score_detections_empty():
    planted_detected, fp_count = score_detections([], "neural networks improve safety")
    assert planted_detected is False
    assert fp_count == 0
