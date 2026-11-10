"""Deploys the backend to Modal:  modal deploy modal_app.py  (run from backend/)."""

import modal

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_pyproject("pyproject.toml", optional_dependencies=["embeddings"])
    .env({"RULEPACK_DIR": "/rulepacks", "FILES_DIR": "/tmp/files"})
    .add_local_dir("../rulepacks", "/rulepacks")
    .add_local_python_source("app")
    .add_local_dir("app/seed/files", "/root/app/seed/files")
)

app = modal.App("rulecollision-backend", image=image, secrets=[modal.Secret.from_name("rulecollision")])


@app.function(min_containers=1)
@modal.concurrent(max_inputs=50)
@modal.asgi_app()
def api():
    from app.main import app as web_app

    return web_app
