"""Tests for the Flask app. Run with:  python test_app.py   (or: python -m pytest)"""
import io

import app as klarsom
import config

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32      # signature only: the app checks signatures, it does not decode


def form(**overrides):
    data = {**config.PRESETS["medium"], **config.DEFAULT_OPTIONS}
    data.update(overrides)
    return {k: str(v) for k, v in data.items()}


def post(client, data, image=None):
    if image is not None:
        data = {**data, "reference_image": (io.BytesIO(image[1]), image[0])}
    return client.post("/", data=data, content_type="multipart/form-data")


def token_of(html):
    return html.split("/plot/")[1].split("/")[0]


def test_health_and_home_page():
    client = klarsom.app.test_client()
    assert client.get("/health").get_json() == {"status": "ok"}
    page = client.get("/")
    assert page.status_code == 200 and b"KlaerSom" not in page.data and "KlærSøm".encode() in page.data
    assert b"1897" not in page.data          # no invented heritage claims


def test_valid_post_returns_five_pieces_and_working_downloads():
    client = klarsom.app.test_client()
    html = post(client, form()).get_data(as_text=True)
    assert html.count('class="piece"') == 5
    token = token_of(html)
    assert client.get(f"/plot/{token}/0").data.startswith(b"\x89PNG")
    assert client.get(f"/download/{token}/0/svg").data.lstrip().startswith((b"<?xml", b"<svg"))
    assert client.get(f"/download/{token}/1/pdf").data.startswith(b"%PDF")
    assert client.get(f"/download/{token}/all.pdf").data.startswith(b"%PDF")
    csv_text = client.get(f"/download/{token}/coordinates.csv").data.decode("utf-8-sig")
    assert csv_text.splitlines()[0] == "piece,point,type,x_cm,y_cm,meaning" and "curve dot" in csv_text


def test_invalid_inputs_are_rejected_with_messages():
    client = klarsom.app.test_client()
    for bad in ({"bust": "abc"}, {"bust": "5"}, {"bust": "nan"}, {"neckline": "hacker"}, {"skirt_style": ""},
                {"waist": "150", "bust": "92"}):
        html = post(client, form(**bad)).get_data(as_text=True)
        assert 'class="error"' in html and 'class="piece"' not in html, bad


def test_impossible_geometry_shows_friendly_error_not_a_crash():
    html = post(klarsom.app.test_client(), form(shoulder_width=20)).get_data(as_text=True)
    assert "Could not draft this pattern" in html


def test_changing_options_changes_the_generated_output():
    client = klarsom.app.test_client()
    a = post(client, form(neckline="square")).get_data(as_text=True)
    b = post(client, form(neckline="shallow")).get_data(as_text=True)
    assert "Square neckline corner" in a and "Square neckline corner" not in b


def test_image_upload_is_validated_by_content_not_name():
    client = klarsom.app.test_client()
    ok = post(client, form(), image=("dress.png", PNG)).get_data(as_text=True)
    assert "/reference/" in ok
    token = ok.split("/reference/")[1].split('"')[0]
    assert client.get(f"/reference/{token}").mimetype == "image/png"
    fake = post(client, form(), image=("dress.png", b"<script>alert(1)</script>")).get_data(as_text=True)
    assert "could not be recognised" in fake and 'class="piece"' not in fake


def test_unknown_tokens_and_formats_return_404():
    client = klarsom.app.test_client()
    assert client.get("/plot/nope/0").status_code == 404
    token = token_of(post(client, form()).get_data(as_text=True))
    assert client.get(f"/download/{token}/0/exe").status_code == 404
    assert client.get(f"/download/{token}/99/png").status_code == 404
    assert client.get("/reference/" + token).status_code == 404     # no image was uploaded


def test_store_keeps_only_recent_designs():
    client = klarsom.app.test_client()
    for _ in range(klarsom.MAX_STORED + 2):
        post(client, form())
    assert len(klarsom.STORE) == klarsom.MAX_STORED


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    for name, fn in tests:
        fn()
        print("PASS", name)
    print(f"{len(tests)} app tests passed.")
