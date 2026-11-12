from app import add, slugify


def test_add():
    assert add(2, 3) == 5


def test_slugify():
    assert slugify("Stratus Lab Service") == "stratus-lab-service"
