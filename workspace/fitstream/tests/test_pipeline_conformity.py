"""
Pipeline Conformity Tests
Verify that all pipelines follow enterprise patterns:
  - Consistent constructor signature
  - pipeline_name attribute
  - Structured error handling (no bare except)
  - Proper logging
"""

import ast
import os
import pytest
from pathlib import Path


PIPELINE_DIR = Path(__file__).parent.parent / "fitstream" / "core" / "pipelines"
PIPELINE_FILES = [
    f for f in PIPELINE_DIR.glob("*.py")
    if f.name not in ("__init__.py", "base.py")
]


class TestPipelineStructure:
    """Every pipeline file must follow the standard structure."""
    
    @pytest.mark.parametrize("pipeline_file", PIPELINE_FILES, ids=lambda f: f.stem)
    def test_has_pipeline_class(self, pipeline_file: Path) -> None:
        """Each pipeline file must contain at least one class with 'Pipeline' in the name."""
        source = pipeline_file.read_text()
        tree = ast.parse(source)
        classes = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and "Pipeline" in node.name
        ]
        assert len(classes) >= 1, f"{pipeline_file.name} has no Pipeline class"
    
    @pytest.mark.parametrize("pipeline_file", PIPELINE_FILES, ids=lambda f: f.stem)
    def test_has_pipeline_name(self, pipeline_file: Path) -> None:
        """Each pipeline class should have a pipeline_name attribute."""
        source = pipeline_file.read_text()
        assert "pipeline_name" in source, f"{pipeline_file.name} missing pipeline_name"
    
    @pytest.mark.parametrize("pipeline_file", PIPELINE_FILES, ids=lambda f: f.stem)
    def test_has_init_with_config(self, pipeline_file: Path) -> None:
        """Each pipeline must accept config and model_manager in __init__."""
        source = pipeline_file.read_text()
        assert "def __init__" in source, f"{pipeline_file.name} missing __init__"
        assert "config" in source, f"{pipeline_file.name} __init__ missing config param"
        assert "model_manager" in source or "ModelManager" in source
    
    @pytest.mark.parametrize("pipeline_file", PIPELINE_FILES, ids=lambda f: f.stem)
    def test_no_bare_except(self, pipeline_file: Path) -> None:
        """No bare 'except:' without exception type."""
        source = pipeline_file.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # node.type is None for bare 'except:'
                assert node.type is not None, (
                    f"{pipeline_file.name} line {node.lineno}: "
                    f"bare 'except:' found — always specify exception type"
                )
    
    @pytest.mark.parametrize("pipeline_file", PIPELINE_FILES, ids=lambda f: f.stem)
    def test_has_docstring(self, pipeline_file: Path) -> None:
        """Each pipeline file must have a module docstring."""
        source = pipeline_file.read_text()
        tree = ast.parse(source)
        docstring = ast.get_docstring(tree)
        assert docstring is not None, f"{pipeline_file.name} missing module docstring"
    
    @pytest.mark.parametrize("pipeline_file", PIPELINE_FILES, ids=lambda f: f.stem)
    def test_imports_loguru(self, pipeline_file: Path) -> None:
        """All pipelines must use structured logging."""
        source = pipeline_file.read_text()
        assert "from loguru import logger" in source, (
            f"{pipeline_file.name} must import loguru logger for structured logging"
        )


class TestNoGlobalState:
    """Verify no pipeline creates global mutable state."""
    
    @pytest.mark.parametrize("pipeline_file", PIPELINE_FILES, ids=lambda f: f.stem)
    def test_no_module_level_mutable_state(self, pipeline_file: Path) -> None:
        """No module-level mutable variables (dicts, lists) outside of constants."""
        source = pipeline_file.read_text()
        tree = ast.parse(source)
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        # Allow UPPER_CASE constants and _ prefixed
                        if name.isupper() or name.startswith("_"):
                            continue
                        # Reject module-level mutable assignment
                        if isinstance(node.value, (ast.List, ast.Dict)):
                            pytest.fail(
                                f"{pipeline_file.name}: module-level mutable var '{name}' "
                                f"on line {node.lineno}. Use class attributes or constants."
                            )


class TestBasePipeline:
    """Test the abstract base class."""
    
    def test_cannot_instantiate_directly(self) -> None:
        from fitstream.core.pipelines.base import BasePipeline
        with pytest.raises(TypeError, match="abstract"):
            BasePipeline()
    
    def test_subclass_must_implement_execute(self) -> None:
        from fitstream.core.pipelines.base import BasePipeline
        from fitstream.core.interfaces import GenerationRequest, GenerationResult
        
        class IncompletePipeline(BasePipeline):
            pipeline_name = "incomplete"
            # Missing _execute!
        
        with pytest.raises(TypeError):
            IncompletePipeline()
    
    def test_valid_subclass(self) -> None:
        from fitstream.core.pipelines.base import BasePipeline
        from fitstream.core.interfaces import GenerationRequest, GenerationResult
        
        class ValidPipeline(BasePipeline):
            pipeline_name = "valid"
            
            def _execute(self, request: GenerationRequest) -> GenerationResult:
                return GenerationResult(success=True, video_path="/test.mp4")
        
        pipeline = ValidPipeline()
        assert pipeline.pipeline_name == "valid"
        
        result = pipeline.generate(GenerationRequest(prompt="test"))
        assert result.success is True
        assert result.pipeline == "valid"
        assert result.generation_time > 0


class TestCodeQualityMetrics:
    """Aggregate quality checks."""
    
    def test_total_pipeline_count(self) -> None:
        """We should have exactly 9 pipeline files (excluding base and __init__)."""
        assert len(PIPELINE_FILES) == 9, (
            f"Expected 9 pipelines, found {len(PIPELINE_FILES)}: "
            f"{[f.stem for f in PIPELINE_FILES]}"
        )
    
    def test_no_circular_imports_in_pipelines(self) -> None:
        """No pipeline should import from api layer."""
        for f in PIPELINE_FILES:
            source = f.read_text()
            assert "from fitstream.api" not in source, (
                f"{f.name} imports from api layer — violates dependency direction"
            )
            assert "import fitstream.api" not in source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
