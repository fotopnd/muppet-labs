from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch


def test_train_pair_calls_trainer_and_saves(tmp_path: Path) -> None:
    fake_texts = ["prompt [SEP] response"] * 20
    fake_labels = [0, 1] * 10

    mock_ds = MagicMock()
    mock_ds.__len__ = MagicMock(return_value=20)

    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": [[1, 2, 3]] * 20, "attention_mask": [[1, 1, 1]] * 20}

    mock_model = MagicMock()
    mock_trainer = MagicMock()
    mock_trainer_instance = MagicMock()
    mock_trainer.return_value = mock_trainer_instance

    with (
        patch("llm_safety_training.train_pair.load_hhrlhf_binary", return_value=(fake_texts[:10], fake_labels[:10])),
        patch("llm_safety_training.train_pair.split_wildguard") as mock_split,
        patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer),
        patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
        patch("transformers.Trainer", mock_trainer),
    ):
        mock_split.return_value = MagicMock(
            pair_train_texts=fake_texts[10:],
            pair_train_labels=fake_labels[10:],
            pair_eval_texts=fake_texts[:5],
            pair_eval_labels=fake_labels[:5],
        )

        from llm_safety_training.train_pair import train

        train(tmp_path, epochs=1, batch_size=4)

    mock_trainer_instance.train.assert_called_once()
    mock_trainer_instance.save_model.assert_called_once_with(str(tmp_path))
