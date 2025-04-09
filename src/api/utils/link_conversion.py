from typing import Any, Dict, List, Union

from src.scrapper.models_dto import LinkDTO, TagDTO
from src.scrapper.schemas import LinkResponse


def _normalize_filters(filters_value: Union[str, List[str], None]) -> List[str]:
    """Normalizes the filters value to a list of strings."""
    match filters_value:
        case str():
            return filters_value.split(",") if filters_value else []
        case list():
            return [str(f) for f in filters_value]
        case _:
            return []


def _normalize_tags(tags: List[Any]) -> List[str]:
    """Normalizes the tags to a list of strings."""
    converted_tags: List[str] = []
    for tag in tags:
        match tag:
            case str():
                converted_tags.append(tag)
            case {"name": tag_name}:
                converted_tags.append(tag_name)
            case TagDTO(tag_name=tag_name):
                converted_tags.append(tag_name)
            case _:
                converted_tags.append(str(tag))
    return converted_tags


def convert_link_dto_to_response(link_dto: LinkDTO) -> LinkResponse:
    """Converts a LinkDTO object to a LinkResponse object.

    This function normalizes the 'tags' and 'filters' fields to ensure they are correctly formatted
    for the LinkResponse schema.

    Args:
        link_dto: The LinkDTO object to convert.

    Returns:
        A LinkResponse object with the converted data.

    """
    link_dict: Dict[str, Any] = link_dto.model_dump()

    link_dict["tags"] = _normalize_tags(link_dict.get("tags", []))
    link_dict["filters"] = _normalize_filters(link_dict.get("filters"))

    return LinkResponse(**link_dict)
