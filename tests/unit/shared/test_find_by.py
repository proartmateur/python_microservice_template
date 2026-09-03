from src.shared.domain.find_by import FindByCriteria, FindByOperator, FindByResult


def test_find_by_types_keep_validated_criteria_and_result() -> None:
    criteria = FindByCriteria("name", FindByOperator.STARTS_WITH, "ada")
    result = FindByResult(items=["Ada"], next_position=None, has_next=False)

    assert criteria.operator is FindByOperator.STARTS_WITH
    assert result.items == ["Ada"]
