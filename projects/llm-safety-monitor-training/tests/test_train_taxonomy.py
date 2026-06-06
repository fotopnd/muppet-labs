from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from llm_safety_training.datasets import NUM_HARM_CATEGORIES


def test_train_taxonomy_calls_trainer_and_saves(tmp_path: Path) -> None:
    fake_texts = ["prompt [SEP] response"] * 20
    fake_labels = [[0] * NUM_HARM_CATEGORIES for _ in range(20)]
    fake_labels[0][0] = 1  # at least one positive

    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": [[1, 2]] * 20, "attention_mask": [[1, 1]] * 20}
    mock_model = MagicMock()
    mock_model.config = MagicMock()
    mock_trainer = MagicMock()
    mock_trainer_instance = MagicMock()
    mock_trainer.return_value = mock_trainer_instance

    with (
        patch("llm_safety_training.train_taxonomy.split_wildguard") as mock_split,
        patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer),
        patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
        patch("transformers.Trainer", mock_trainer),
    ):
        mock_split.return_value = MagicMock(
            taxonomy_train_texts=fake_texts[:16],
            taxonomy_train_labels=fake_labels[:16],
            taxonomy_eval_texts=fake_texts[16:],
            taxonomy_eval_labels=fake_labels[16:],
        )

        from llm_safety_training.train_taxonomy import train

        train(tmp_path, epochs=1, batch_size=4)

    # Verify multi_label_classification problem type was set
    assert mock_model.config.problem_type == "multi_label_classification"
    mock_trainer_instance.train.assert_called_once()
    mock_trainer_instance.save_model.assert_called_once_with(str(tmp_path))
