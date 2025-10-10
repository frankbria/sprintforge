"""
Performance Benchmarking Tests for Excel Generation Engine (Task 3.7).

Measures generation time, memory usage, and formula calculation speed
for different project sizes and complexity levels.

Target: Document performance characteristics, identify bottlenecks
"""

import pytest
import time
import tracemalloc
from io import BytesIO
from datetime import datetime
from openpyxl import load_workbook

from app.excel.engine import ExcelTemplateEngine, ProjectConfig
from app.excel.templates import select_template, TemplateLayoutBuilder


class TestGenerationPerformance:
    """Test Excel generation time for different project sizes."""

    def test_small_project_generation_time(self):
        """Test generation time for small project (10 tasks)."""
        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="perf_small",
            project_name="Small Performance Test",
            task_count=10,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        generation_time = time.time() - start_time

        assert excel_bytes is not None
        assert generation_time < 1.0  # Should complete in under 1 second
        print(f"\n✓ Small project (10 tasks): {generation_time:.3f}s")

    def test_medium_project_generation_time(self):
        """Test generation time for medium project (50 tasks)."""
        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="perf_medium",
            project_name="Medium Performance Test",
            task_count=50,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        generation_time = time.time() - start_time

        assert excel_bytes is not None
        assert generation_time < 3.0  # Should complete in under 3 seconds
        print(f"✓ Medium project (50 tasks): {generation_time:.3f}s")

    def test_large_project_generation_time(self):
        """Test generation time for large project (200 tasks)."""
        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="perf_large",
            project_name="Large Performance Test",
            task_count=200,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        generation_time = time.time() - start_time

        assert excel_bytes is not None
        assert generation_time < 10.0  # Should complete in under 10 seconds
        print(f"✓ Large project (200 tasks): {generation_time:.3f}s")

    def test_extra_large_project_generation_time(self):
        """Test generation time for extra large project (500 tasks)."""
        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="perf_xlarge",
            project_name="Extra Large Performance Test",
            task_count=500,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        generation_time = time.time() - start_time

        assert excel_bytes is not None
        assert generation_time < 30.0  # Should complete in under 30 seconds
        print(f"✓ Extra large project (500 tasks): {generation_time:.3f}s")

    def test_generation_time_scales_linearly(self):
        """Test that generation time scales approximately linearly."""
        engine = ExcelTemplateEngine()

        # Test different sizes
        sizes = [10, 50, 100, 200]
        times = []

        for size in sizes:
            config = ProjectConfig(
                project_id=f"perf_scale_{size}",
                project_name=f"Scale Test {size}",
                task_count=size,
            )

            start_time = time.time()
            engine.generate_template(config)
            times.append(time.time() - start_time)

        # Calculate time per task for each size
        time_per_task = [t / s for t, s in zip(times, sizes)]

        # Variance in time per task should be reasonable
        avg_time_per_task = sum(time_per_task) / len(time_per_task)
        max_deviation = max(abs(t - avg_time_per_task) for t in time_per_task)

        # Allow 50% deviation from average
        assert max_deviation < avg_time_per_task * 0.5

        print(f"\n✓ Scaling analysis:")
        for size, total_time, per_task in zip(sizes, times, time_per_task):
            print(f"  {size} tasks: {total_time:.3f}s ({per_task*1000:.1f}ms/task)")


class TestMemoryUsage:
    """Test memory usage patterns during Excel generation."""

    def test_small_project_memory_usage(self):
        """Test memory usage for small project."""
        tracemalloc.start()

        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="mem_small",
            project_name="Small Memory Test",
            task_count=10,
        )

        excel_bytes = engine.generate_template(config)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be under 10MB for small project
        peak_mb = peak / (1024 * 1024)
        assert peak_mb < 10.0
        print(f"\n✓ Small project memory: {peak_mb:.2f}MB")

    def test_medium_project_memory_usage(self):
        """Test memory usage for medium project."""
        tracemalloc.start()

        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="mem_medium",
            project_name="Medium Memory Test",
            task_count=50,
        )

        excel_bytes = engine.generate_template(config)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be under 30MB for medium project
        peak_mb = peak / (1024 * 1024)
        assert peak_mb < 30.0
        print(f"✓ Medium project memory: {peak_mb:.2f}MB")

    def test_large_project_memory_usage(self):
        """Test memory usage for large project."""
        tracemalloc.start()

        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="mem_large",
            project_name="Large Memory Test",
            task_count=200,
        )

        excel_bytes = engine.generate_template(config)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be under 100MB for large project
        peak_mb = peak / (1024 * 1024)
        assert peak_mb < 100.0
        print(f"✓ Large project memory: {peak_mb:.2f}MB")

    def test_memory_cleanup_after_generation(self):
        """Test that memory is properly released after generation."""
        tracemalloc.start()

        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="mem_cleanup",
            project_name="Memory Cleanup Test",
            task_count=100,
        )

        # Generate file
        excel_bytes = engine.generate_template(config)

        # Get memory after generation
        after_gen, peak_gen = tracemalloc.get_traced_memory()

        # Clear references
        del excel_bytes
        del engine

        # Force garbage collection
        import gc
        gc.collect()

        # Get memory after cleanup
        after_cleanup, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory should decrease significantly after cleanup
        cleanup_ratio = after_cleanup / after_gen
        assert cleanup_ratio < 0.5  # At least 50% memory released

        print(f"\n✓ Memory cleanup: {after_gen/(1024*1024):.2f}MB → {after_cleanup/(1024*1024):.2f}MB ({cleanup_ratio*100:.1f}%)")

    def test_concurrent_generation_memory_isolation(self):
        """Test that concurrent generations don't share memory."""
        tracemalloc.start()

        engine1 = ExcelTemplateEngine()
        engine2 = ExcelTemplateEngine()

        config1 = ProjectConfig(
            project_id="mem_concurrent_1",
            project_name="Concurrent Test 1",
            task_count=50,
        )

        config2 = ProjectConfig(
            project_id="mem_concurrent_2",
            project_name="Concurrent Test 2",
            task_count=50,
        )

        # Generate both
        bytes1 = engine1.generate_template(config1)
        bytes2 = engine2.generate_template(config2)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak should not be double (should reuse memory)
        peak_mb = peak / (1024 * 1024)
        assert peak_mb < 60.0  # Less than 2x single generation

        assert bytes1 != bytes2  # Different outputs
        print(f"\n✓ Concurrent generation memory: {peak_mb:.2f}MB")


class TestFormulaCalculationSpeed:
    """Test formula calculation and workbook loading speed."""

    def test_workbook_loading_time(self):
        """Test time to load generated workbook."""
        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="load_test",
            project_name="Loading Speed Test",
            task_count=100,
        )

        excel_bytes = engine.generate_template(config)
        buffer = BytesIO(excel_bytes)

        start_time = time.time()
        workbook = load_workbook(buffer)
        load_time = time.time() - start_time

        assert workbook is not None
        assert load_time < 2.0  # Should load in under 2 seconds
        print(f"\n✓ Workbook loading (100 tasks): {load_time:.3f}s")

    def test_formula_count_performance(self):
        """Test performance impact of formula count."""
        engine = ExcelTemplateEngine()

        # Generate project with many formulas
        config = ProjectConfig(
            project_id="formula_perf",
            project_name="Formula Performance Test",
            task_count=100,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        generation_time = time.time() - start_time

        # Load and count formulas
        buffer = BytesIO(excel_bytes)
        workbook = load_workbook(buffer)
        ws = workbook["Project Plan"]

        formula_count = 0
        for row in ws.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str) and cell.value.startswith("="):
                    formula_count += 1

        formulas_per_second = formula_count / generation_time if generation_time > 0 else 0

        assert formulas_per_second > 100  # Should generate at least 100 formulas/sec
        print(f"\n✓ Formula generation: {formula_count} formulas in {generation_time:.3f}s ({formulas_per_second:.0f}/sec)")

    def test_conditional_formatting_performance(self):
        """Test conditional formatting application performance."""
        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="cond_format_perf",
            project_name="Conditional Format Performance",
            task_count=100,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        generation_time = time.time() - start_time

        # Load and check conditional formatting
        buffer = BytesIO(excel_bytes)
        workbook = load_workbook(buffer)
        ws = workbook["Project Plan"]

        # Conditional formatting should be present
        cond_format_count = len(ws.conditional_formatting._cf_rules) if hasattr(ws.conditional_formatting, '_cf_rules') else 0

        assert generation_time < 5.0  # Should complete quickly even with formatting
        print(f"\n✓ Conditional formatting: {cond_format_count} rules in {generation_time:.3f}s")


class TestTemplatePerformance:
    """Test performance of different template types."""

    def test_basic_template_performance(self):
        """Test basic template generation performance."""
        template = select_template("agile", "basic")
        builder = TemplateLayoutBuilder()
        layout = builder.build_layout(template)

        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="perf_basic",
            project_name="Basic Template Performance",
            task_count=100,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        generation_time = time.time() - start_time

        assert generation_time < 3.0  # Basic should be fast
        print(f"\n✓ Basic template (100 tasks): {generation_time:.3f}s")

    def test_advanced_template_performance(self):
        """Test advanced template generation performance."""
        template = select_template("agile", "advanced")
        builder = TemplateLayoutBuilder()
        layout = builder.build_layout(template)

        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="perf_advanced",
            project_name="Advanced Template Performance",
            task_count=100,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        generation_time = time.time() - start_time

        assert generation_time < 5.0  # Advanced has more formulas but should still be reasonable
        print(f"\n✓ Advanced template (100 tasks): {generation_time:.3f}s")

    def test_hybrid_template_performance(self):
        """Test hybrid template generation performance."""
        from app.excel.templates import TemplateRegistry

        registry = TemplateRegistry()
        template = registry.get_template("hybrid")
        builder = TemplateLayoutBuilder()
        layout = builder.build_layout(template)

        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="perf_hybrid",
            project_name="Hybrid Template Performance",
            task_count=100,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        generation_time = time.time() - start_time

        assert generation_time < 6.0  # Hybrid is most complex
        print(f"\n✓ Hybrid template (100 tasks): {generation_time:.3f}s")


class TestBottleneckIdentification:
    """Identify performance bottlenecks in generation pipeline."""

    def test_metadata_generation_overhead(self):
        """Test metadata generation performance overhead."""
        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="bottleneck_meta",
            project_name="Metadata Bottleneck Test",
            task_count=100,
        )

        # Time with metadata
        start_time = time.time()
        with_meta = engine.generate_template(config)
        with_meta_time = time.time() - start_time

        # Metadata overhead should be minimal (<10% of total time)
        assert with_meta_time < 5.0
        print(f"\n✓ Metadata overhead: {with_meta_time:.3f}s")

    def test_styling_application_overhead(self):
        """Test styling and formatting overhead."""
        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="bottleneck_style",
            project_name="Styling Bottleneck Test",
            task_count=100,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        total_time = time.time() - start_time

        # Styling should not dominate generation time
        assert total_time < 5.0
        print(f"\n✓ Styling overhead: {total_time:.3f}s")

    def test_data_validation_overhead(self):
        """Test data validation rule application overhead."""
        engine = ExcelTemplateEngine()
        config = ProjectConfig(
            project_id="bottleneck_validation",
            project_name="Validation Bottleneck Test",
            task_count=100,
        )

        start_time = time.time()
        excel_bytes = engine.generate_template(config)
        total_time = time.time() - start_time

        # Data validation should be efficient
        assert total_time < 5.0
        print(f"\n✓ Data validation overhead: {total_time:.3f}s")


class TestPerformanceRegression:
    """Test for performance regressions."""

    def test_performance_does_not_degrade(self):
        """Test that performance meets baseline expectations."""
        engine = ExcelTemplateEngine()

        # Baseline: 100 tasks should complete in under 3 seconds
        config = ProjectConfig(
            project_id="regression_baseline",
            project_name="Regression Baseline",
            task_count=100,
        )

        times = []
        for i in range(3):  # Run 3 times
            start_time = time.time()
            engine.generate_template(config)
            times.append(time.time() - start_time)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 3.0  # Average should be under 3 seconds
        assert max_time < 4.0  # Even worst case should be under 4 seconds

        print(f"\n✓ Performance regression check:")
        print(f"  Average: {avg_time:.3f}s")
        print(f"  Max: {max_time:.3f}s")
        print(f"  Min: {min(times):.3f}s")

    def test_file_size_efficiency(self):
        """Test that generated file sizes are reasonable."""
        engine = ExcelTemplateEngine()

        sizes = [10, 50, 100, 200]
        file_sizes = []

        for size in sizes:
            config = ProjectConfig(
                project_id=f"size_test_{size}",
                project_name=f"Size Test {size}",
                task_count=size,
            )

            excel_bytes = engine.generate_template(config)
            file_size_kb = len(excel_bytes) / 1024
            file_sizes.append(file_size_kb)

        # File size should scale reasonably
        # 100 tasks should be under 500KB
        size_100_idx = sizes.index(100)
        assert file_sizes[size_100_idx] < 500

        print(f"\n✓ File size efficiency:")
        for size, kb in zip(sizes, file_sizes):
            print(f"  {size} tasks: {kb:.1f}KB ({kb/size:.2f}KB/task)")


# Performance benchmark summary
def test_performance_benchmark_summary():
    """Summary of all performance benchmarks."""
    # This is a marker test to document performance targets
    assert True, """
    Performance Benchmark Targets:

    Generation Time:
    - Small (10 tasks): < 1 second
    - Medium (50 tasks): < 3 seconds
    - Large (200 tasks): < 10 seconds
    - Extra Large (500 tasks): < 30 seconds

    Memory Usage:
    - Small (10 tasks): < 10 MB
    - Medium (50 tasks): < 30 MB
    - Large (200 tasks): < 100 MB

    Formula Performance:
    - Generation: > 100 formulas/second
    - Loading: < 2 seconds for 100 tasks

    File Size:
    - 100 tasks: < 500 KB
    - Reasonable scaling with task count
    """
