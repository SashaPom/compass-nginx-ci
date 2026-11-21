def test_default_nginx_config(host):
    check = host.run("nginx -t")
    assert check.rc == 0, check.stderr


def test_demo_page_marker(host):
    page = host.file("/usr/share/nginx/html/index.html")
    assert page.is_file and page.contains("devops6-demo")
