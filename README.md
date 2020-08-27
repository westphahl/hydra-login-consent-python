Hydra login/consent provider - Python
======================================

This is an example implementation for the User Login and Consent flow of 
[ORY Hydra](https://www.ory.sh/docs/hydra/) version 1.7.x in Python.

**Requirements: Python >= 3.7**

This example is using the official
[ory-hydra-client](https://github.com/ory/sdk/tree/master/clients/hydra/python) Python library.

Running locally
---------------

Use the official Hydra Container image:

```shell
docker run \
    -it \
    --rm \
    --network="host" \
    -e "DSN=memory" \
    -e "URLS_SELF_ISSUER=http://127.0.0.1:4444/" \
    -e "URLS_CONSENT=http://127.0.0.1:5000/consent" \
    -e "URLS_LOGIN=http://127.0.0.1:5000/login" \
    -e "LOG_LEAK_SENSITIVE_VALUES=true" \
    --name hydra \
    -p 4445:4445 \
    -p 4444:4444 \
    oryd/hydra:v1.7 \
    serve all --dangerous-force-http
```

Afterwards you can install the dependencies and run the example application:


```shell
$ pip install -r requirements.txt
$ flask run
```


## Testing an example flow

```sh
docker exec hydra \
    hydra clients create \
    --endpoint http://127.0.0.1:4445 \
    --id auth-code-client \
    --secret secret \
    --grant-types authorization_code,refresh_token \
    --response-types code,id_token \
    --scope openid,offline \
    --callbacks http://127.0.0.1:5555/callback
```

```sh
docker exec hydra \
    hydra token user \
    --client-id auth-code-client \
    --client-secret secret \
    --endpoint http://127.0.0.1:4444/ \
    --port 5555 \
    --scope openid,offline \
    --audience auth-code-client
```

See also the instructions in the
[5 minute tutorial](https://www.ory.sh/docs/hydra/5min-tutorial) for testing
the various [OAuth 2.0 grant types](https://oauth.net/2/grant-types/).
