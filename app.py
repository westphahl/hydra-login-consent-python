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

from hydra_client import HydraAdmin


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


class LoginView(View):

    methods = "GET", "POST"

    def render_form(self, form, **context):
        return render_template("login.html", form=form, **context)

    def dispatch_request(self):
        form = LoginForm()
        hydra = HydraAdmin(HYDRA_ADMIN_URL)

        challenge = request.args.get("login_challenge") or form.challenge.data
        if not challenge:
            abort(400)

        login_request = hydra.login_request(challenge)
        if request.method == "GET":
            return self.get(login_request, form, challenge)
        elif request.method == "POST":
            return self.post(login_request, form, challenge)
        abort(405)

    def get(self, login_request, form, challenge):
        if login_request.skip:
            redirect_to = login_request.accept(subject=login_request.subject)
            return redirect(redirect_to)
        else:
            form.challenge.data = challenge
        return self.render_form(form)

    def post(self, login_request, form, challenge):
        if form.validate():
            if form.login.data:
                if form.user.data == "foo@bar.com" and form.password.data == "password":
                    subject = form.user.data
                    redirect_to = login_request.accept(
                        subject=subject, remember=form.remember.data
                    )
                else:
                    # TODO: show error message
                    return self.render_form(form)
            else:
                redirect_to = login_request.reject(error="user_decline")
            return redirect(redirect_to)
        return self.render_form(form)


class ConsentView(View):

    methods = "GET", "POST"

    def render_form(self, form, **context):
        return render_template("consent.html", form=form, **context)

    def dispatch_request(self):
        form = ConsentForm()
        hydra = HydraAdmin(HYDRA_ADMIN_URL)

        challenge = request.args.get("consent_challenge") or form.challenge.data
        if not challenge:
            abort(400)

        consent_request = hydra.consent_request(challenge)
        form.requested_scope.choices = [(s, s) for s in consent_request.requested_scope]

        if request.method == "GET":
            return self.get(form, consent_request)
        elif request.method == "POST":
            return self.post(form, consent_request)
        abort(405)

    def get(self, form, consent_request):
        if consent_request.skip:
            redirect_to = consent_request.accept(
                grant_scope=consent_request.requested_scope,
                grant_access_token_audience=consent_request.requested_access_token_audience,
            )
            return redirect(redirect_to)
        else:
            form.challenge.data = consent_request.challenge

        return self.render_form(
            form, user=consent_request.subject, client=consent_request.client
        )

    def post(self, form, consent_request):
        if form.validate():
            if form.accept.data:
                session = {
                    "access_token": {},
                    "id_token": {
                        "sub": "248289761001",
                        "name": "Jane Doe",
                        "given_name": "Jane",
                        "family_name": "Doe",
                        "preferred_username": "j.doe",
                        "email": "janedoe@example.com",
                        "picture": "",
                    },
                }
                redirect_to = consent_request.accept(
                    grant_scope=form.requested_scope.data,
                    grant_access_token_audience=consent_request.requested_access_token_audience,
                    session=session,
                    remember=form.remember.data,
                )
            else:
                redirect_to = consent_request.accept(error="user_decline")
            return redirect(redirect_to)
        else:
            # TODO: show error message
            pass
        return self.render_form(form)


app = Flask(__name__)
app.secret_key = os.urandom(16)
csrf = CSRFProtect(app)

app.add_url_rule("/login", view_func=LoginView.as_view("login"))
app.add_url_rule("/consent", view_func=ConsentView.as_view("consent"))
