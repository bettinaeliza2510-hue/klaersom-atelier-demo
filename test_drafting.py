"""Tests for the drafting engine. Run with:  python test_drafting.py   (or: python -m pytest)"""
import config
from drafting import (classify_body_type, draft_dress, draft_front_bodice, offset_polygon, path_length,
                      polygon_area, self_intersects)

MEDIUM = config.PRESETS["medium"]


def test_all_presets_draft_five_valid_pieces():
    for name, m in config.PRESETS.items():
        dress = draft_dress(m)
        assert [p["id"] for p in dress["pieces"]] == ["front_bodice", "back_bodice", "skirt", "sleeve", "sash"], name
        for p in dress["pieces"]:
            assert not self_intersects(p["outline"]), (name, p["id"])
            assert not self_intersects(p["cut_outline"]), (name, p["id"])
            assert polygon_area(p["outline"]) > 50


def test_drafting_is_deterministic():
    a = draft_dress(MEDIUM)["pieces"][0]["outline"]
    b = draft_dress(MEDIUM)["pieces"][0]["outline"]
    assert a == b


def test_offset_of_rectangle_grows_by_allowance_on_every_side():
    cut = offset_polygon([(0, 0), (10, 0), (10, 5), (0, 5)], 1.5)
    assert abs(polygon_area(cut) - (10 + 3) * (5 + 3)) < 1e-9


def test_fold_edge_gets_no_allowance_and_hem_gets_more():
    skirt = draft_dress(MEDIUM, seam_allowance=1.5)["pieces"][2]
    assert min(x for x, _ in skirt["cut_outline"]) == 0.0          # fold stays on x = 0
    top = min(y for _, y in skirt["cut_outline"])
    bottom = max(y for _, y in skirt["cut_outline"])
    assert abs(top - (-1.5)) < 1e-9                                  # waist seam allowance
    assert abs(bottom - (skirt["dims"]["skirt_length"] + 3.0)) < 1e-9  # 3 cm hem


def test_zero_allowance_leaves_outline_unchanged():
    outline = draft_front_bodice(MEDIUM)["outline"]
    for p, q in zip(outline, offset_polygon(outline, 0)):
        assert abs(p[0] - q[0]) < 1e-9 and abs(p[1] - q[1]) < 1e-9


def test_self_intersection_detector_catches_a_bow_tie():
    assert self_intersects([(0, 0), (10, 10), (10, 0), (0, 10)])
    assert not self_intersects([(0, 0), (10, 0), (10, 10), (0, 10)])


def test_neckline_choice_changes_geometry():
    square = draft_front_bodice(MEDIUM, "square")
    shallow = draft_front_bodice(MEDIUM, "shallow")
    assert square["outline"] != shallow["outline"]
    assert "B" in square["points"] and "B" not in shallow["points"]
    assert any(label.startswith("A1") for label in shallow["labels"])   # curve dots


def test_skirt_fullness_and_style_change_the_skirt():
    full = draft_dress(MEDIUM, skirt_fullness=2.2)["pieces"][2]["dims"]
    light = draft_dress(MEDIUM, skirt_fullness=1.2)["pieces"][2]["dims"]
    straight = draft_dress(MEDIUM, skirt_style="straight")["pieces"][2]["dims"]
    assert full["top_width"] > light["top_width"]
    assert straight["fullness_ratio"] == 1.0 and straight["top_width"] == 19.5   # waist / 4 + 0.5


def test_puff_changes_sleeve_cap_length():
    plain = draft_dress(MEDIUM, puff_fullness=1.0)["pieces"][3]
    puffy = draft_dress(MEDIUM, puff_fullness=1.8)["pieces"][3]
    assert path_length(puffy, "A", "C") > path_length(plain, "A", "C")


def test_front_and_back_seams_match_for_every_preset_and_neckline():
    for m in config.PRESETS.values():
        for neckline in config.NECKLINES:
            checks = {c["label"]: c for c in draft_dress(m, neckline=neckline)["checks"]}
            assert checks["Shoulder seam, front vs back"]["status"] == "ok"
            assert checks["Side seam, front vs back"]["status"] == "ok"


def test_sleeve_cap_check_warns_when_cap_cannot_reach_armhole():
    tiny_arm = {**MEDIUM, "upper_arm": 15}
    checks = {c["label"]: c for c in draft_dress(tiny_arm, puff_fullness=1.0)["checks"]}
    assert checks["Sleeve cap vs armhole"]["status"] == "warn"


def test_impossible_measurements_raise_clear_errors():
    for bad in ({**MEDIUM, "shoulder_width": 20}, {**MEDIUM, "front_length": 25}, {**MEDIUM, "dress_length": 45}):
        try:
            draft_dress(bad)
        except ValueError as exc:
            assert str(exc)
        else:
            raise AssertionError(f"expected ValueError for {bad}")


def test_body_type_label_is_one_of_the_known_labels():
    assert classify_body_type(MEDIUM) in {"Hourglass-like", "Pear / triangle-like",
                                          "Inverted-triangle-like", "Balanced proportions"}


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    for name, fn in tests:
        fn()
        print("PASS", name)
    print(f"{len(tests)} engine tests passed.")
