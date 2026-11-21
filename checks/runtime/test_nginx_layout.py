import pytest


@pytest.mark.parametrize(
    "path",
    ("/etc/nginx/conf.d/default.conf", "/srv/compass/index.html", "/srv/compass/health.json"),
    ids=("server-block", "homepage", "health-document"),
)
def test_image_contains_file(host, path):
    assert host.file(path).is_file, f"Missing file: {path}"


def test_running_nginx_config_loads(host):
    result = host.run("nginx -t")
    assert result.rc == 0, result.stderr


def test_packaged_homepage_matches_release(host, target):
    assert host.file("/srv/compass/index.html").contains(target.release)
