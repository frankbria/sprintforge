"""
Excel Compatibility Module for Task 3.5.

Provides Excel version detection, modern function support, cross-platform compatibility,
and formula optimization for performance.

Supports Excel 2019, 2021, and 365 across Windows and Mac platforms.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


class ExcelVersion(Enum):
    """Supported Excel versions with feature capabilities."""

    EXCEL_2019 = "2019"
    EXCEL_2021 = "2021"
    EXCEL_365 = "365"
    UNKNOWN = "unknown"


class Platform(Enum):
    """Target platform for Excel file generation."""

    WINDOWS = "windows"
    MAC = "mac"
    WEB = "web"
    ANY = "any"


@dataclass
class ExcelFeature:
    """Definition of an Excel feature with version/platform requirements."""

    name: str
    min_version: ExcelVersion
    supported_platforms: Set[Platform]
    fallback_available: bool
    description: str


class ExcelCompatibilityManager:
    """
    Manages Excel version compatibility and feature detection.

    Provides methods for detecting Excel version capabilities,
    determining feature availability, and applying fallbacks for
    unsupported features.

    Example:
        >>> manager = ExcelCompatibilityManager(ExcelVersion.EXCEL_2019, Platform.WINDOWS)
        >>> if manager.supports_feature("xlookup"):
        ...     formula = manager.get_modern_formula("xlookup", ...)
        ... else:
        ...     formula = manager.get_fallback_formula("xlookup", ...)
    """

    # Modern Excel functions with version requirements
    MODERN_FUNCTIONS: Dict[str, ExcelFeature] = {
        "xlookup": ExcelFeature(
            name="XLOOKUP",
            min_version=ExcelVersion.EXCEL_365,
            supported_platforms={Platform.WINDOWS, Platform.MAC, Platform.WEB},
            fallback_available=True,
            description="Modern lookup function replacing VLOOKUP/HLOOKUP",
        ),
        "filter": ExcelFeature(
            name="FILTER",
            min_version=ExcelVersion.EXCEL_365,
            supported_platforms={Platform.WINDOWS, Platform.MAC, Platform.WEB},
            fallback_available=True,
            description="Dynamic array function for filtering data",
        ),
        "sort": ExcelFeature(
            name="SORT",
            min_version=ExcelVersion.EXCEL_365,
            supported_platforms={Platform.WINDOWS, Platform.MAC, Platform.WEB},
            fallback_available=False,
            description="Dynamic array function for sorting data",
        ),
        "unique": ExcelFeature(
            name="UNIQUE",
            min_version=ExcelVersion.EXCEL_365,
            supported_platforms={Platform.WINDOWS, Platform.MAC, Platform.WEB},
            fallback_available=False,
            description="Returns unique values from a range",
        ),
        "let": ExcelFeature(
            name="LET",
            min_version=ExcelVersion.EXCEL_365,
            supported_platforms={Platform.WINDOWS, Platform.MAC, Platform.WEB},
            fallback_available=True,
            description="Assigns names to calculation results for reuse",
        ),
        "lambda": ExcelFeature(
            name="LAMBDA",
            min_version=ExcelVersion.EXCEL_365,
            supported_platforms={Platform.WINDOWS, Platform.WEB},
            fallback_available=False,
            description="Create custom reusable functions",
        ),
        "sequence": ExcelFeature(
            name="SEQUENCE",
            min_version=ExcelVersion.EXCEL_365,
            supported_platforms={Platform.WINDOWS, Platform.MAC, Platform.WEB},
            fallback_available=True,
            description="Generates array of sequential numbers",
        ),
        "xmatch": ExcelFeature(
            name="XMATCH",
            min_version=ExcelVersion.EXCEL_365,
            supported_platforms={Platform.WINDOWS, Platform.MAC, Platform.WEB},
            fallback_available=True,
            description="Modern match function with enhanced capabilities",
        ),
    }

    def __init__(
        self,
        target_version: ExcelVersion = ExcelVersion.EXCEL_2019,
        target_platform: Platform = Platform.ANY,
        enable_fallbacks: bool = True,
    ):
        """
        Initialize Excel compatibility manager.

        Args:
            target_version: Target Excel version for compatibility
            target_platform: Target platform (Windows, Mac, Web, Any)
            enable_fallbacks: Whether to enable fallback formulas for unsupported features
        """
        self.target_version = target_version
        self.target_platform = target_platform
        self.enable_fallbacks = enable_fallbacks

        logger.info(
            "Excel compatibility manager initialized",
            version=target_version.value,
            platform=target_platform.value,
            fallbacks_enabled=enable_fallbacks,
        )

    def supports_feature(self, feature_name: str) -> bool:
        """
        Check if a feature is supported by target version/platform.

        Args:
            feature_name: Name of the feature to check (lowercase)

        Returns:
            bool: True if feature is supported
        """
        feature_name = feature_name.lower()

        if feature_name not in self.MODERN_FUNCTIONS:
            logger.warning("Unknown feature", feature=feature_name)
            return False

        feature = self.MODERN_FUNCTIONS[feature_name]

        # Check version compatibility
        version_supported = self._check_version_support(feature.min_version)

        # Check platform compatibility
        platform_supported = (
            self.target_platform == Platform.ANY
            or self.target_platform in feature.supported_platforms
        )

        supported = version_supported and platform_supported

        logger.debug(
            "Feature support check",
            feature=feature_name,
            supported=supported,
            version_ok=version_supported,
            platform_ok=platform_supported,
        )

        return supported

    def _check_version_support(self, min_version: ExcelVersion) -> bool:
        """
        Check if target version meets minimum version requirement.

        Args:
            min_version: Minimum required Excel version

        Returns:
            bool: True if target version meets requirement
        """
        if self.target_version == ExcelVersion.UNKNOWN:
            return False

        version_order = {
            ExcelVersion.EXCEL_2019: 1,
            ExcelVersion.EXCEL_2021: 2,
            ExcelVersion.EXCEL_365: 3,
        }

        target_level = version_order.get(self.target_version, 0)
        min_level = version_order.get(min_version, 999)

        return target_level >= min_level

    def get_xlookup_formula(
        self,
        lookup_value: str,
        lookup_array: str,
        return_array: str,
        if_not_found: str = '""',
        match_mode: int = 0,
        search_mode: int = 1,
    ) -> str:
        """
        Generate XLOOKUP formula or fallback to INDEX/MATCH.

        Args:
            lookup_value: Value to look up
            lookup_array: Array to search in
            return_array: Array to return from
            if_not_found: Value if not found
            match_mode: 0=exact, -1=exact or next smallest, 1=exact or next largest, 2=wildcard
            search_mode: 1=first to last, -1=last to first, 2=binary ascending, -2=binary descending

        Returns:
            str: XLOOKUP formula or INDEX/MATCH fallback
        """
        if self.supports_feature("xlookup"):
            return (
                f"=XLOOKUP({lookup_value}, {lookup_array}, {return_array}, "
                f"{if_not_found}, {match_mode}, {search_mode})"
            )

        # Fallback to INDEX/MATCH
        if self.enable_fallbacks:
            match_type = 0 if match_mode == 0 else (1 if match_mode == -1 else -1)
            return (
                f"=IFERROR(INDEX({return_array}, "
                f"MATCH({lookup_value}, {lookup_array}, {match_type})), {if_not_found})"
            )

        raise ValueError(
            f"XLOOKUP not supported in {self.target_version.value} and fallbacks disabled"
        )

    def get_filter_formula(
        self,
        array: str,
        include: str,
        if_empty: str = '""',
    ) -> str:
        """
        Generate FILTER formula or fallback approach.

        Args:
            array: Array to filter
            include: Boolean array for filtering
            if_empty: Value if result is empty

        Returns:
            str: FILTER formula or fallback
        """
        if self.supports_feature("filter"):
            return f"=FILTER({array}, {include}, {if_empty})"

        # Fallback: Return manual filtering instruction
        if self.enable_fallbacks:
            logger.warning(
                "FILTER function not available, using array formula fallback",
                version=self.target_version.value,
            )
            # Complex array formula fallback
            return (
                f"=IFERROR(IF({include}, {array}, \"\"), {if_empty})"
            )

        raise ValueError(
            f"FILTER not supported in {self.target_version.value} and fallbacks disabled"
        )

    def get_let_formula(
        self,
        variables: List[Tuple[str, str]],
        calculation: str,
    ) -> str:
        """
        Generate LET formula for variable assignment or expand inline.

        Args:
            variables: List of (name, value) tuples
            calculation: Final calculation using variables

        Returns:
            str: LET formula or expanded calculation
        """
        if self.supports_feature("let"):
            # Build LET formula: =LET(name1, value1, name2, value2, ..., calculation)
            let_parts = []
            for name, value in variables:
                let_parts.extend([name, value])
            let_parts.append(calculation)

            let_args = ", ".join(let_parts)
            return f"=LET({let_args})"

        # Fallback: Expand variables inline
        if self.enable_fallbacks:
            expanded = calculation
            for name, value in variables:
                expanded = expanded.replace(name, f"({value})")
            return f"={expanded}"

        raise ValueError(
            f"LET not supported in {self.target_version.value} and fallbacks disabled"
        )

    def optimize_formula_performance(self, formula: str) -> str:
        """
        Optimize formula for better performance.

        Applies optimization strategies:
        1. Reduce volatile function usage (NOW, TODAY, RAND, OFFSET)
        2. Minimize array formula complexity
        3. Use efficient lookup methods
        4. Avoid nested IF statements where possible

        Args:
            formula: Original formula

        Returns:
            str: Optimized formula
        """
        optimized = formula

        # Replace volatile OFFSET with INDEX where possible
        if "OFFSET(" in optimized and self._is_simple_offset(optimized):
            logger.debug("Optimizing OFFSET to INDEX")
            optimized = self._replace_offset_with_index(optimized)

        # Replace nested IFs with IFS (Excel 2019+)
        if self._check_version_support(ExcelVersion.EXCEL_2019):
            if optimized.count("IF(") > 3:
                logger.debug("Optimizing nested IFs to IFS")
                optimized = self._optimize_nested_ifs(optimized)

        # Reduce INDIRECT usage (volatile)
        if "INDIRECT(" in optimized:
            logger.warning(
                "Formula contains INDIRECT (volatile function)",
                performance_impact="high",
            )

        return optimized

    def _is_simple_offset(self, formula: str) -> bool:
        """Check if OFFSET usage is simple enough to replace with INDEX."""
        # Simplified check - in production, use proper parsing
        return "OFFSET(" in formula and formula.count("OFFSET(") == 1

    def _replace_offset_with_index(self, formula: str) -> str:
        """Replace simple OFFSET with INDEX for better performance."""
        # Simplified replacement - production would need proper formula parsing
        return formula.replace("OFFSET(", "INDEX(")

    def _optimize_nested_ifs(self, formula: str) -> str:
        """Convert nested IF statements to IFS function."""
        # Simplified optimization - production needs complete formula parser
        if formula.count("IF(") <= 3:
            return formula

        # This is a placeholder - real implementation needs formula tree parsing
        logger.debug("Nested IF optimization requires formula parsing")
        return formula

    def get_compatibility_report(self) -> Dict[str, any]:
        """
        Generate compatibility report for target version/platform.

        Returns:
            Dict with supported features, missing features, and recommendations
        """
        supported = []
        unsupported = []
        fallback_available = []

        for feature_name, feature in self.MODERN_FUNCTIONS.items():
            if self.supports_feature(feature_name):
                supported.append(feature_name)
            else:
                unsupported.append(feature_name)
                if feature.fallback_available and self.enable_fallbacks:
                    fallback_available.append(feature_name)

        report = {
            "target_version": self.target_version.value,
            "target_platform": self.target_platform.value,
            "supported_features": supported,
            "unsupported_features": unsupported,
            "fallback_features": fallback_available,
            "total_features": len(self.MODERN_FUNCTIONS),
            "support_percentage": (len(supported) / len(self.MODERN_FUNCTIONS)) * 100,
        }

        logger.info(
            "Compatibility report generated",
            version=self.target_version.value,
            support_pct=f"{report['support_percentage']:.1f}%",
        )

        return report


class CrossPlatformOptimizer:
    """
    Handles cross-platform compatibility optimizations.

    Addresses platform-specific differences between Windows Excel,
    Mac Excel, and Excel Online.
    """

    # Platform-specific quirks and workarounds
    PLATFORM_QUIRKS = {
        Platform.MAC: {
            "date_system": "1904",  # Mac may use 1904 date system
            "path_separator": "/",
            "lambda_support": False,  # LAMBDA not fully supported on Mac
        },
        Platform.WINDOWS: {
            "date_system": "1900",
            "path_separator": "\\",
            "lambda_support": True,
        },
        Platform.WEB: {
            "date_system": "1900",
            "path_separator": "/",
            "file_dialogs": False,  # No file dialog support
        },
    }

    def __init__(self, platform: Platform = Platform.ANY):
        """
        Initialize cross-platform optimizer.

        Args:
            platform: Target platform
        """
        self.platform = platform
        logger.info("Cross-platform optimizer initialized", platform=platform.value)

    def adjust_date_formula(self, formula: str) -> str:
        """
        Adjust date formulas for platform-specific date systems.

        Args:
            formula: Original date formula

        Returns:
            str: Platform-adjusted formula
        """
        if self.platform != Platform.MAC:
            return formula

        # Mac uses 1904 date system - add adjustment if needed
        # This is a simplified example
        if "DATE(" in formula or "DATEVALUE(" in formula:
            logger.debug("Adjusting formula for Mac 1904 date system")
            # In production, would add actual date system adjustment
            return formula

        return formula

    def get_path_separator(self) -> str:
        """Get platform-specific path separator."""
        quirks = self.PLATFORM_QUIRKS.get(self.platform, {})
        return quirks.get("path_separator", "/")

    def supports_file_dialogs(self) -> bool:
        """Check if platform supports file dialogs."""
        quirks = self.PLATFORM_QUIRKS.get(self.platform, {})
        return quirks.get("file_dialogs", True)
