
alias rd := run-docker
alias rdd := run-docker-detach
alias sd := stop-docker

run:
    uv run src/main.py

run-docker:
    docker compose up

run-docker-detach:
    docker compose up -d

stop-docker:
    docker compose down
