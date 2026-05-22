from urllib.parse import urlparse
from flask import redirect as flask_redirect
from flask import request, get_flashed_messages, render_template
from flask.wrappers import Response
from bson.json_util import dumps
from fame.common.config import fame_config
from web.views.helpers import get_fame_url


def should_render_as_html():
    best_accept = request.accept_mimetypes.best_match(["text/html", "application/json"])
    api_key = bool(request.headers.get("X-API-KEY"))
    token = bool(request.headers.get("Autorization")) and request.headers.get(
        "Autorization"
    ).lower().startswith("bearer ")

    return best_accept == "text/html" and not api_key and not token


def render_json(data):
    body = dumps(data)

    return Response(response=body, mimetype='application/json')


def render_html(data, template, ctx=None):
    ctx = ctx or {
        'data': data
    }

    return render_template(template, **ctx)


def render(data, template, ctx=None):
    if should_render_as_html():
        return render_html(data, template, ctx)
    else:
        return render_json(data)


def is_allowed_domain(target):
    if not target:
        return False

    normalized_target = target.replace("\\", "/")
    parsed = urlparse(normalized_target)

    if parsed.scheme and not parsed.netloc:
        return False

    if not parsed.scheme and not parsed.netloc:
        return True

    allowed_netlocs = set()
    for url in fame_config.fame_url.strip().split(" "):
        url = url.strip()
        if url:
            netloc = urlparse(url).netloc
            if netloc:
                allowed_netlocs.add(netloc)

    return parsed.netloc in allowed_netlocs


def redirect(data, path):
    if should_render_as_html():
        if is_allowed_domain(path):
            return flask_redirect(path)
        return flask_redirect("/")

    return render_json(data)


def validation_error(path=None):
    if should_render_as_html():
        if is_allowed_domain(path):
            return flask_redirect(path)
        return flask_redirect("/")

    return render_json({'errors': get_flashed_messages()})
