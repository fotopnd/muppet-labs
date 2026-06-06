from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


def test_train_prompt_calls_trainer_and_saves(tmp_path: Path) -> None:
    fake_texts = ["adversarial prompt"] * 20
    fake_labels = [1, 0] * 10

    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": [[1, 2]] * 20, "attention_mask": [[1, 1]] * 20}
    mock_model = MagicMock()
    mock_trainer = MagicMock()
    mock_trainer_instance = MagicMock()
    mock_trainer.return_value = mock_trainer_instance

    with (
        patch(
            "llm_safety_training.train_prompt.build_prompt_detector_dataset",
            return_value=(fake_texts[:16], fake_labels[:16], fake_texts[16:], fake_labels[16:]),
        ),
        patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer),
        patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
        patch("transformers.Trainer", mock_trainer),
    ):
        from llm_safety_training.train_prompt import train

        train(tmp_path, epochs=1, batch_size=4)

    mock_trainer_instance.train.assert_called_once()
    mock_trainer_instance.save_model.assert_called_once_with(str(tmp_path))
