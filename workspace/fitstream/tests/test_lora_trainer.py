"""Tests for LoRA trainer."""

import os
import tempfile
import pytest
from fitstream.core.lora_trainer import LoRATrainer, LoRAConfig


@pytest.fixture
def trainer():
    with tempfile.TemporaryDirectory() as d:
        yield LoRATrainer(loras_dir=d)


@pytest.fixture
def sample_images():
    paths = []
    for i in range(5):
        from PIL import Image
        img = Image.new("RGB", (100, 100), (i * 50, 100, 200))
        p = tempfile.mktemp(suffix=".jpg")
        img.save(p)
        paths.append(p)
    yield paths
    for p in paths:
        if os.path.exists(p):
            os.unlink(p)


class TestLoRAConfig:
    def test_valid_config(self, sample_images):
        c = LoRAConfig(name="test", trigger_word="ohwx", training_images=sample_images)
        errors = c.validate()
        assert len(errors) == 0

    def test_too_few_images(self):
        c = LoRAConfig(name="test", trigger_word="ohwx", training_images=["a.jpg"])
        errors = c.validate()
        assert any("3 training images" in e for e in errors)

    def test_missing_name(self, sample_images):
        c = LoRAConfig(name="", trigger_word="ohwx", training_images=sample_images)
        errors = c.validate()
        assert any("Name" in e for e in errors)

    def test_invalid_rank(self, sample_images):
        c = LoRAConfig(name="test", trigger_word="ohwx", training_images=sample_images, lora_rank=7)
        errors = c.validate()
        assert any("rank" in e.lower() for e in errors)

    def test_to_dict(self, sample_images):
        c = LoRAConfig(name="test", trigger_word="ohwx", training_images=sample_images)
        d = c.to_dict()
        assert d["name"] == "test"
        assert d["num_images"] == 5


class TestLoRATrainer:
    def test_create_config(self, trainer, sample_images):
        config = trainer.create_config(
            name="my-person", trigger_word="ohwx person",
            training_images=sample_images, num_steps=500,
        )
        assert config.name == "my-person"
        assert os.path.exists(os.path.join(config.output_dir, "config.json"))

    def test_train_creates_script(self, trainer, sample_images):
        config = trainer.create_config(
            name="train-test", trigger_word="ohwx",
            training_images=sample_images,
        )
        result = trainer.train(config)
        assert result.success is True
        assert os.path.exists(os.path.join(config.output_dir, "train.py"))
        assert os.path.exists(os.path.join(config.output_dir, "dataset"))

    def test_list_loras(self, trainer, sample_images):
        config = trainer.create_config("lora1", "ohwx", sample_images)
        trainer.train(config)
        loras = trainer.list_loras()
        assert len(loras) == 1
        assert loras[0]["name"] == "lora1"

    def test_delete_lora(self, trainer, sample_images):
        config = trainer.create_config("del-me", "ohwx", sample_images)
        trainer.train(config)
        assert trainer.delete_lora("del-me") is True
        assert len(trainer.list_loras()) == 0

    def test_delete_nonexistent(self, trainer):
        assert trainer.delete_lora("nope") is False

    def test_invalid_config_raises(self, trainer):
        with pytest.raises(ValueError):
            trainer.create_config("", "ohwx", ["a.jpg"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
