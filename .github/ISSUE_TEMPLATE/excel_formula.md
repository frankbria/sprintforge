---
name: Excel Formula Contribution
about: Suggest new Excel formulas for project management calculations
title: '[FORMULA] '
labels: 'enhancement, excel, formulas, good first issue'
assignees: ''
---

## Formula Type
- [ ] Dependency calculations
- [ ] Resource management
- [ ] Monte Carlo simulation
- [ ] Sprint calculations
- [ ] Risk assessment
- [ ] Cost estimation
- [ ] Progress tracking
- [ ] Other: ___________

## Formula Description
**What calculation does this formula perform?**
Clear description of what the formula calculates and why it's useful for project management.

**Use Case:**
Specific scenario where this formula would be helpful.

## Proposed Formula
```excel
=YOUR_FORMULA_HERE($parameter1, $parameter2)
```

**Parameters:**
- `$parameter1`: Description of first parameter
- `$parameter2`: Description of second parameter

**Example:**
```excel
=IF(ISBLANK(E4), D5, MAX(D5, E4 + 1))
```

## Excel Compatibility
- [ ] Excel 2019+
- [ ] Excel 365 specific features
- [ ] Cross-platform compatible (Windows/Mac)

**Functions Used:**
List Excel functions used in your formula (e.g., IF, XLOOKUP, SUMIF)

## Template Location
**Where should this formula be added?**
- [ ] New template file: `backend/app/excel/components/templates/[name].json`
- [ ] Existing template: `backend/app/excel/components/templates/[existing].json`

**Suggested file name:** ___________

## Testing Scenarios
**How can this formula be tested?**
1. Test scenario 1
2. Test scenario 2
3. Edge cases to consider

## Additional Context
**References:**
- Links to project management methodology
- Academic papers or industry standards
- Similar implementations in other tools

**Implementation Notes:**
- Any complex logic that needs explanation
- Performance considerations
- Dependencies on other formulas

**Screenshots/Examples:**
Add any visual examples or screenshots of the formula in action.

---

## For Contributors

**Getting Started:**
1. See [DEVELOPMENT.md](../../DEVELOPMENT.md) for setup instructions
2. Formula templates are in: `backend/app/excel/components/templates/`
3. Tests go in: `backend/tests/excel/test_[formula_name].py`
4. Add documentation to the formula JSON file

**Template Format:**
```json
{
  "_metadata": {
    "description": "Brief description of formula category",
    "contributor": "@your-github-username",
    "version": "1.0"
  },
  "formula_name": {
    "formula": "=YOUR_FORMULA($param1, $param2)",
    "description": "What this formula does",
    "parameters": {
      "param1": "Description of parameter 1",
      "param2": "Description of parameter 2"
    },
    "example": "=REAL_EXAMPLE(D5, E4)"
  }
}
```

**Need Help?**
- Join our [Discord](https://discord.gg/sprintforge) for real-time help
- Check existing formulas for examples
- Ask questions in this issue!