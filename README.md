Hydra login/consent provider - Python
======================================

This is an example implementation for the User Login and Consent flow of 
[ORY Hydra](https://www.ory.sh/docs/hydra/) version 1.0.x in Python.

**Requirements: Python >= 3.7**

This example is using my
[hydra-client](https://github.com/westphahl/hydra-client) Python library.

Running locally
---------------

Use the official Hydra Container image:

```shell
docker run \
    -it \
    --rm \
    --network="host" \
    -e "DSN=memory" \
    -e "URLS_SELF_ISSUER=http://localhost:4444/" \
    -e "URLS_CONSENT=http://localhost:5000/consent" \
    -e "URLS_LOGIN=http://localhost:5000/login" \
    --name hydra \
    -p 4445:4445 \
    -p 4444:4444 \
    oryd/hydra:v1.0 \
    serve all --dangerous-force-http
```

Afterwards you can install the dependencies and run the example application:


```shell
$ pip install -r requirements.txt
$ flask run
```

Follow the instructions in the
[5 minute tutorial](https://www.ory.sh/docs/hydra/5min-tutorial) for testing
the various [OAuth 2.0 grant types](https://oauth.net/2/grant-types/).
