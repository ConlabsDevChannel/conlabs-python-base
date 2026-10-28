import pytest

from pydantic import ValidationError

from app.core.pagination.schemas import PageRequest
from app.core.pagination.helpers import create_page


def test_page_request_defaults():
    paging = PageRequest()

    assert paging.page == 1
    assert paging.size == 20
    assert paging.offset == 0


def test_page_request_offset():
    paging = PageRequest(page=3, size=10)

    assert paging.offset == 20


@pytest.mark.parametrize(
    "page,size",
    [
        (0, 20),
        (-1, 20),
        (1, 0),
        (1, 101),
    ],
)
def test_invalid_page_request(page, size):
    with pytest.raises(ValidationError):
        PageRequest(page=page, size=size)


def test_create_page():
    paging = PageRequest(page=2, size=10)

    result = create_page(
        items=[11, 12, 13],
        total_elements=35,
        request=paging,
    )

    assert result.items == [11, 12, 13]
    assert result.total_pages == 4
    assert result.has_next is True
    assert result.has_previous is True


def test_empty_page():
    result = create_page(
        items=[],
        total_elements=0,
        request=PageRequest(),
    )

    assert result.total_pages == 0
    assert result.has_next is False
    assert result.has_previous is False