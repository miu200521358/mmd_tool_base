import pytest


def test_parse_str():
    from mlib.domain.logger import round_str

    assert "1" == round_str(1)
    assert "1.23" == round_str(1.23)
    assert "1.23444" == round_str(1.23444444)
    assert "1.23457" == round_str(1.23456789)
    assert "abc" == round_str("abc")


def test_parse2str():
    from mlib.domain.logger import parse2str

    class ChildSample:
        def __init__(self, _y, _b) -> None:
            self.y = _y
            self.b = _b

        def __str__(self):
            return parse2str(self)

    class Sample:
        def __init__(self, _x, _a, _y, _b) -> None:
            self.x = _x
            self.a = _a
            self.child = ChildSample(_y, _b)

        def __str__(self):
            return parse2str(self)

    assert parse2str(ChildSample(2, "sss")) == "ChildSample[y=2, b=sss]"
    # cSpell:disable
    assert parse2str(ChildSample(1.23456789, "abcdefghijklmn")) == "ChildSample[y=1.23457, b=abcdefghijklmn]"
    # cSpell:enable
    assert parse2str(Sample(2, "sss", 4.5, "xyz")) == "Sample[x=2, a=sss, child=ChildSample[y=4.5, b=xyz]]"


if __name__ == "__main__":
    pytest.main()
