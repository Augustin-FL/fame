import urllib.parse
import os
import uuid
import requests
from importlib import import_module
from flask import Blueprint, request, redirect, session, render_template
from flask_login import logout_user

from web.views.helpers import prevent_csrf
from fame.common.config import fame_config
from web.auth.oidc.user_management import (
    authenticate,
    check_oidc_settings_present,
    ClaimMappingError,
)

auth = Blueprint("", __name__, template_folder="templates")


@auth.route("/oidc-login", methods=["GET", "POST"])
@prevent_csrf
def login():
    check_oidc_settings_present()
    code = request.args.get("code", "")
    if code:
        auth = (fame_config.oidc_client_id, fame_config.oidc_client_secret)
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": fame_config.fame_url + "/oidc-login",
        }
        token = requests.post(
            fame_config.oidc_token_endpoint, auth=auth, data=data
        ).json()
        if not "access_token" in token:
            # invalid "code" given, invalid clientID/Secret in config, etc..
            error_description = token.get("error_description", "")
            return render_template(
                "auth_error.html", error_description=error_description
            )
        try:
            authenticate(token["access_token"])
            session["_flashes"].clear()  # Clear any message asking to log in

            redir = request.args.get("next", "/")
            return redirect(urllib.parse.urljoin(fame_config.fame_url, redir))

        except ClaimMappingError as e:
            return render_template("auth_error.html", error_description=e.msg)
    else:
        args = {
            "client_id": fame_config.oidc_client_id,
            "response_type": "code",
            "scope": fame_config.oidc_requested_scopes,
            "redirect_uri": fame_config.fame_url + "/oidc-login",
            "nonce": uuid.uuid4().hex,
        }
        login_url = (
            fame_config.oidc_authorize_endpoint + "?" + urllib.parse.urlencode(args)
        )
        return redirect(login_url)


@auth.route("/logout")
def logout():
    logout_user()
    return render_template("logout.html")