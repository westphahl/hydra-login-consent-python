import os

import requests
from flask import abort, Flask, redirect, render_template, request
from flask.views import View
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import (
    BooleanField,
    HiddenField,
    PasswordField,
    SelectMultipleField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired


HYDRA_ADMIN_URL = "http://localhost:4445"


class DataRequiredIf(DataRequired):
    field_flags = ("optional",)

    def __init__(self, check_field, *args, **kwargs):
        self.check_field = check_field
        super().__init__(*args, **kwargs)

    def __call__(self, form, field):
        check_field = form._fields.get(self.check_field)
        if check_field is None:
            raise RuntimeError(f"No field called '{self.check_field}'")
        if check_field.data:
            super().__call__(form, field)


class LoginForm(FlaskForm):
    login = SubmitField("login")
    abort = SubmitField("abort")
    user = StringField("user", validators=[DataRequiredIf("login")])
    password = PasswordField("password", validators=[DataRequiredIf("login")])
    remember = BooleanField("remember")
    challenge = HiddenField("challenge", validators=[DataRequired()])


class ConsentForm(FlaskForm):
    accept = SubmitField("accept")
    decline = SubmitField("decline")
    challenge = HiddenField("challenge", validators=[DataRequired()])
    requested_scope = SelectMultipleField("requested scopes")
    remember = BooleanField("remember")


class HydraClient:
    def __init__(self):
        self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def get_login_request(self, challenge):
        url = f"{HYDRA_ADMIN_URL}/oauth2/auth/requests/login/{challenge}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def accept_login_request(
        self, challenge, subject, remember=False, remember_for=3600
    ):
        url = f"{HYDRA_ADMIN_URL}/oauth2/auth/requests/login/{challenge}/accept"
        data = {"subject": subject, "remember": remember, "remember_for": remember_for}
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()

    def reject_login_request(self, challenge, error):
        url = f"{HYDRA_ADMIN_URL}/oauth2/auth/requests/login/{challenge}/reject"
        data = {"error": error}
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_consent_request(self, challenge):
        url = f"{HYDRA_ADMIN_URL}/oauth2/auth/requests/consent/{challenge}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def accept_consent_request(
        self,
        challenge,
        grant_scope,
        grant_access_token_audience,
        session,
        remember=False,
        remember_for=3600,
    ):
        url = f"{HYDRA_ADMIN_URL}/oauth2/auth/requests/consent/{challenge}/accept"
        data = {
            "grant_access_token_audience": grant_access_token_audience,
            "grant_scope": grant_scope,
            "remember": remember,
            "remember_for": remember_for,
            "session": session,
        }
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()

    def reject_consent_request(self, challenge, error):
        url = f"{HYDRA_ADMIN_URL}/oauth2/auth/requests/consent/{challenge}/reject"
        data = {"error": error}
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()


class LoginView(View):

    methods = "GET", "POST"

    def render_form(self, form, **context):
        return render_template("login.html", form=form, **context)

    def dispatch_request(self):
        form = LoginForm()
        hydra = HydraClient()

        challenge = request.args.get("login_challenge") or form.challenge.data
        if not challenge:
            abort(400)

        if request.method == "GET":
            return self.get(hydra, form, challenge)
        elif request.method == "POST":
            return self.post(hydra, form, challenge)
        abort(405)

    def get(self, hydra, form, challenge):
        login_request = hydra.get_login_request(challenge)
        if login_request.get("skip", False):
            response = hydra.accept_login_request(challenge, login_request.subject)
            return redirect(response["redirect_to"])
        else:
            form.challenge.data = challenge
        return self.render_form(form)

    def post(self, hydra, form, challenge):
        if form.validate():
            if form.login.data:
                if form.user.data == "foo@bar.com" and form.password.data == "password":
                    subject = form.user.data
                    response = hydra.accept_login_request(
                        challenge, subject=subject, remember=form.remember.data
                    )
                else:
                    # TODO: show error message
                    return self.render_form(form)
            else:
                response = hydra.reject_login_request(challenge, "user_decline")
            return redirect(response["redirect_to"])
        return self.render_form(form)


class ConsentView(View):

    methods = "GET", "POST"

    def render_form(self, form, **context):
        return render_template("consent.html", form=form, **context)

    def dispatch_request(self):
        form = ConsentForm()
        hydra = HydraClient()

        challenge = request.args.get("consent_challenge") or form.challenge.data
        if not challenge:
            abort(400)

        consent_request = hydra.get_consent_request(challenge)
        form.requested_scope.choices = [
            (s, s) for s in consent_request.get("requested_scope", [])
        ]

        if request.method == "GET":
            return self.get(hydra, form, challenge, consent_request)
        elif request.method == "POST":
            return self.post(hydra, form, challenge, consent_request)
        abort(405)

    def get(self, hydra, form, challenge, consent_request):
        if consent_request.get("skip", False):
            response = hydra.accept_consent_request(
                challenge,
                consent_request.get("requested_scope"),
                consent_request.get("requested_access_token_audience"),
                {},
            )
            return redirect(response["redirect_to"])
        else:
            form.challenge.data = challenge

        return self.render_form(
            form,
            user=consent_request.get("subject"),
            client=consent_request.get("client"),
        )

    def post(self, hydra, form, challenge, consent_request):
        if form.validate():
            if form.accept.data:
                response = hydra.accept_consent_request(
                    challenge,
                    form.requested_scope.data,
                    consent_request.get("requested_access_token_audience"),
                    {},
                    remember=form.remember.data,
                )
            else:
                response = hydra.reject_consent_request(challenge, "user_decline")
            return redirect(response["redirect_to"])
        else:
            # TODO: show error message
            pass
        return self.render_form(form)


app = Flask(__name__)
app.secret_key = os.urandom(16)
csrf = CSRFProtect(app)

app.add_url_rule("/login", view_func=LoginView.as_view("login"))
app.add_url_rule("/consent", view_func=ConsentView.as_view("consent"))
