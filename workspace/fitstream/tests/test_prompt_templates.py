"""Tests for prompt template library."""

import pytest
from fitstream.core.prompt_templates import PromptTemplateLibrary, PromptTemplate, TEMPLATES


class TestPromptTemplate:
    def test_fill_basic(self):
        t = PromptTemplate(id="test", category="test", name="Test",
                           template="{person} walks in {location}")
        result = t.fill(person="Marie", location="Paris")
        assert "Marie" in result
        assert "Paris" in result

    def test_fill_partial(self):
        """Unfilled variables get replaced with defaults."""
        t = PromptTemplate(id="test", category="test", name="Test",
                           template="{person} walks in {location}")
        result = t.fill(person="Marie")
        assert "Marie" in result
        assert "the person" not in result  # person was filled
        # location should get default replacement
        assert "beautiful setting" in result

    def test_auto_detect_variables(self):
        t = PromptTemplate(id="test", category="test", name="Test",
                           template="{person} wears {garment} in {location}")
        assert "person" in t.variables
        assert "garment" in t.variables
        assert "location" in t.variables


class TestPromptTemplateLibrary:
    def setup_method(self):
        self.lib = PromptTemplateLibrary()

    def test_count(self):
        assert self.lib.count() >= 25  # We defined 25+ templates

    def test_categories(self):
        categories = self.lib.list_categories()
        assert "actions" in categories
        assert "locations" in categories
        assert "emotions" in categories
        assert "camera" in categories
        assert "fashion" in categories
        assert "story" in categories

    def test_get_template(self):
        result = self.lib.get("actions.walk", person="Marie")
        assert result is not None
        assert "Marie" in result

    def test_get_fashion_template(self):
        result = self.lib.get("fashion.runway", person="a model", garment="red gown")
        assert "model" in result
        assert "red gown" in result
        assert "runway" in result

    def test_get_nonexistent(self):
        assert self.lib.get("nonexistent.template") is None

    def test_list_templates(self):
        all_templates = self.lib.list_templates()
        assert len(all_templates) >= 25

    def test_list_by_category(self):
        actions = self.lib.list_templates("actions")
        assert len(actions) >= 5
        for t in actions:
            assert t["category"] == "actions"

    def test_search(self):
        results = self.lib.search("runway")
        assert len(results) >= 1
        assert any("runway" in r["name"].lower() for r in results)

    def test_search_camera(self):
        results = self.lib.search("dolly")
        assert len(results) >= 1

    def test_all_templates_fillable(self):
        """Every template should produce a non-empty string when filled."""
        for template_id in [t.id for t in TEMPLATES]:
            result = self.lib.get(template_id,
                                  person="a young woman",
                                  garment="a blue dress",
                                  location="a sunny garden")
            assert result is not None
            assert len(result) > 10, f"Template {template_id} produced too-short result"

    def test_template_examples_in_list(self):
        """list_templates should include auto-generated examples."""
        templates = self.lib.list_templates("fashion")
        for t in templates:
            assert "example" in t
            assert len(t["example"]) > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
