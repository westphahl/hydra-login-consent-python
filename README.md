Hydra login/consent provider - Python
======================================

This is an example implementation for the User Login and Consent flow of [ORY Hydra](https://www.ory.sh/docs/hydra/) version 1.0.x in Python.

**Requirements: Python >= 3.6**

Running locally
---------------

Use the official [Docker Compose file](https://github.com/ory/hydra/blob/master/docker-compose.yml) from the [Hydra repository](https://github.com/ory/hydra) and comment out the complete `consent` service (official [NodeJS reference implementation](https://github.com/ory/hydra-login-consent-node)).

Make sure to also change the `OAUTH2_LOGIN_URL` and `OAUTH2_CONSENT_URL` in the
Compose file as follows:

```
OAUTH2_CONSENT_URL=http://localhost:5000/consent
OAUTH2_LOGIN_URL=http://localhost:5000/login
```

Afterwards you can install the dependencies and run the example application:


```shell
$ pip install -r requirements.txt
$ flask run
```

Follow the instructions in the [5 minute tutorial](https://www.ory.sh/docs/hydra/5min-tutorial) for testing the various [OAuth 2.0 grant types](https://oauth.net/2/grant-types/).
