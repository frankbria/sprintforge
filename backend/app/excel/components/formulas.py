"""Formula template system for dynamic Excel formula generation.

Provides a JSON-based template system for creating complex Excel formulas
with parameter substitution and validation.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from string import Template

import structlog

logger = structlog.get_logger(__name__)


class FormulaTemplate:
    """
    Formula template manager for loading and applying Excel formula templates.

    Formula templates use Python string.Template syntax with parameter substitution.
    Templates are stored in JSON files and can be dynamically loaded and applied.

    Example template JSON:
        {
          "dependency_fs": {
            "formula": "=IF(ISBLANK($predecessor_finish), $task_start, MAX($task_start, $predecessor_finish + $lag_days))",
            "description": "Finish-to-start dependency calculation",
            "parameters": {
              "predecessor_finish": "Cell reference to predecessor task finish date",
              "task_start": "Cell reference to current task start date",
              "lag_days": "Number of lag days between tasks"
            }
          }
        }

    Usage:
        >>> templates = FormulaTemplate()
        >>> formula = templates.apply_template(
        ...     "dependency_fs",
        ...     predecessor_finish="E2",
        ...     task_start="D3",
        ...     lag_days="0"
        ... )
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize formula template manager.

        Args:
            templates_dir: Directory containing template JSON files.
                          Defaults to app/excel/components/templates/
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"

        self.templates_dir = templates_dir
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all template JSON files from templates directory."""
        if not self.templates_dir.exists():
            logger.warning(
                "Templates directory not found",
                path=str(self.templates_dir),
            )
            return

        template_files = list(self.templates_dir.glob("*.json"))

        for template_file in template_files:
            try:
                with open(template_file, "r") as f:
                    templates = json.load(f)

                # Merge templates from this file
                for name, template_data in templates.items():
                    if not name.startswith("_"):  # Skip metadata entries
                        self.templates[name] = template_data

                logger.debug(
                    "Template file loaded",
                    file=template_file.name,
                    templates_count=len([k for k in templates if not k.startswith("_")]),
                )

            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse template JSON",
                    file=template_file.name,
                    error=str(e),
                )
            except Exception as e:
                logger.error(
                    "Failed to load template file",
                    file=template_file.name,
                    error=str(e),
                )

        logger.info(
            "Formula templates loaded",
            total_templates=len(self.templates),
        )

    def apply_template(self, template_name: str, **parameters: str) -> str:
        """
        Apply a formula template with parameter substitution.

        Args:
            template_name: Name of the template to apply
            **parameters: Template parameters as keyword arguments

        Returns:
            str: Formula with substituted parameters

        Raises:
            KeyError: If template name not found
            ValueError: If required parameters are missing
        """
        if template_name not in self.templates:
            available = ", ".join(self.templates.keys())
            raise KeyError(
                f"Template '{template_name}' not found. Available: {available}"
            )

        template_data = self.templates[template_name]
        formula_template = template_data.get("formula", "")

        if not formula_template:
            raise ValueError(f"Template '{template_name}' has no formula defined")

        # Validate required parameters
        self._validate_parameters(template_name, template_data, parameters)

        # Apply parameter substitution using string.Template
        try:
            template = Template(formula_template)
            formula = template.substitute(parameters)

            logger.debug(
                "Template applied",
                template_name=template_name,
                parameters=parameters,
            )

            return formula

        except KeyError as e:
            raise ValueError(
                f"Missing required parameter for template '{template_name}': {e}"
            )

    def _validate_parameters(
        self, template_name: str, template_data: Dict[str, Any], provided: Dict[str, str]
    ) -> None:
        """
        Validate that all required parameters are provided.

        Args:
            template_name: Name of template being validated
            template_data: Template data dictionary
            provided: Provided parameters

        Raises:
            ValueError: If required parameters are missing
        """
        required_params = template_data.get("parameters", {})

        if not required_params:
            # Extract parameters from formula using regex if not documented
            formula = template_data.get("formula", "")
            required_params = self._extract_parameters(formula)

        # Check for missing parameters
        missing = set(required_params.keys()) - set(provided.keys())

        if missing:
            raise ValueError(
                f"Missing required parameters for template '{template_name}': {', '.join(missing)}"
            )

    def _extract_parameters(self, formula: str) -> Dict[str, str]:
        """
        Extract parameter names from a formula template.

        Args:
            formula: Formula template string

        Returns:
            Dict mapping parameter names to descriptions (empty strings)
        """
        # Find all $parameter_name patterns
        pattern = r"\$([a-zA-Z_][a-zA-Z0-9_]*)"
        matches = re.findall(pattern, formula)

        # Return unique parameters
        return {param: "" for param in set(matches)}

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        Get information about a specific template.

        Args:
            template_name: Name of the template

        Returns:
            Dict with template information (formula, description, parameters)

        Raises:
            KeyError: If template not found
        """
        if template_name not in self.templates:
            raise KeyError(f"Template '{template_name}' not found")

        return self.templates[template_name].copy()

    def list_templates(self) -> List[str]:
        """
        Get list of all available template names.

        Returns:
            List of template names
        """
        return list(self.templates.keys())

    def add_template(
        self,
        name: str,
        formula: str,
        description: str = "",
        parameters: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Add a new formula template programmatically.

        Args:
            name: Template name
            formula: Formula template string with $parameters
            description: Human-readable description
            parameters: Dict mapping parameter names to descriptions
        """
        self.templates[name] = {
            "formula": formula,
            "description": description,
            "parameters": parameters or {},
        }

        logger.debug("Template added", name=name)
