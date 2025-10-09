"""
Formula Template Loader

Loads and applies formula templates from JSON files.
Provides templating system for Excel formulas with parameter substitution.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class FormulaTemplateLoader:
    """
    Loads formula templates from JSON files and applies parameter substitution.

    Usage:
        loader = FormulaTemplateLoader()
        loader.load_template("monte_carlo")
        formula = loader.apply_template("pert_mean", optimistic="10", most_likely="20", pessimistic="30")
    """

    def __init__(self):
        """Initialize the formula template loader."""
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.template_dir = Path(__file__).parent

    def load_template(self, template_name: str) -> None:
        """
        Load a formula template from JSON file.

        Args:
            template_name: Name of the template file (without .json extension)

        Raises:
            FileNotFoundError: If template file doesn't exist
            json.JSONDecodeError: If template file is invalid JSON
        """
        template_path = self.template_dir / f"{template_name}.json"

        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path, 'r') as f:
            self.templates[template_name] = json.load(f)

    def get_template_data(self, template_name: str) -> Dict[str, Any]:
        """
        Get the raw template data for a loaded template.

        Args:
            template_name: Name of the loaded template

        Returns:
            Dict containing the template data

        Raises:
            ValueError: If template hasn't been loaded
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not loaded. Call load_template() first.")

        return self.templates[template_name]

    def apply_template(self, formula_name: str, **params) -> str:
        """
        Apply parameters to a formula template.

        Args:
            formula_name: Name of the formula in the template
            **params: Parameters to substitute in the formula

        Returns:
            Formula string with parameters substituted

        Raises:
            ValueError: If formula not found in any loaded template
        """
        # Search all loaded templates for the formula
        for template_name, template_data in self.templates.items():
            if formula_name in template_data:
                formula_config = template_data[formula_name]
                formula_template = formula_config.get("formula", "")

                # Substitute parameters
                formula = self._substitute_parameters(formula_template, params)
                return formula

        raise ValueError(f"Formula '{formula_name}' not found in any loaded template")

    def _substitute_parameters(self, template: str, params: Dict[str, str]) -> str:
        """
        Substitute parameters in a formula template.

        Args:
            template: Formula template string with $parameter placeholders
            params: Dictionary of parameter names to values

        Returns:
            Formula with parameters substituted
        """
        result = template

        # Sort parameters by length (longest first) to avoid substring conflicts
        # e.g., replace $hours_per_point before $hours
        sorted_params = sorted(params.items(), key=lambda x: len(x[0]), reverse=True)

        # Replace each parameter
        for param_name, param_value in sorted_params:
            placeholder = f"${param_name}"
            result = result.replace(placeholder, str(param_value))

        return result

    def get_formula_metadata(self, formula_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a formula (description, parameters, etc.).

        Args:
            formula_name: Name of the formula

        Returns:
            Dictionary with formula metadata, or None if not found
        """
        for template_data in self.templates.values():
            if formula_name in template_data:
                config = template_data[formula_name].copy()
                # Remove the formula itself, return only metadata
                config.pop("formula", None)
                return config

        return None

    def list_formulas(self, template_name: Optional[str] = None) -> list[str]:
        """
        List all available formulas.

        Args:
            template_name: Optional template name to filter by

        Returns:
            List of formula names
        """
        formulas = []

        if template_name:
            if template_name in self.templates:
                template_data = self.templates[template_name]
                formulas = [k for k in template_data.keys() if not k.startswith("_")]
        else:
            # All formulas from all templates
            for template_data in self.templates.values():
                formulas.extend([k for k in template_data.keys() if not k.startswith("_")])

        return sorted(formulas)

    def get_extension_hooks(self, template_name: str) -> Dict[str, Any]:
        """
        Get extension hooks from a template.

        Args:
            template_name: Name of the template

        Returns:
            Dictionary of extension hooks

        Raises:
            ValueError: If template not loaded
        """
        template_data = self.get_template_data(template_name)
        return template_data.get("_extension_hooks", {})

    def validate_template(self, template_name: str) -> list[str]:
        """
        Validate a loaded template for completeness.

        Args:
            template_name: Name of the template to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if template_name not in self.templates:
            errors.append(f"Template '{template_name}' not loaded")
            return errors

        template_data = self.templates[template_name]

        # Check for metadata
        if "_metadata" not in template_data:
            errors.append("Template missing _metadata section")

        # Check each formula
        for formula_name, config in template_data.items():
            if formula_name.startswith("_"):
                continue  # Skip metadata sections

            if not isinstance(config, dict):
                errors.append(f"Formula '{formula_name}' should be a dictionary")
                continue

            # Check required fields
            if "formula" not in config:
                errors.append(f"Formula '{formula_name}' missing 'formula' field")

            if "description" not in config:
                errors.append(f"Formula '{formula_name}' missing 'description' field")

            # Check parameters documentation
            if "parameters" in config:
                if not isinstance(config["parameters"], dict):
                    errors.append(f"Formula '{formula_name}' parameters should be a dictionary")

        return errors
