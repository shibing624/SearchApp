export ZHIPUAI_API_KEY=
nohup gunicorn -k uvicorn.workers.UvicornWorker "search:create_app()" --bind 0.0.0.0:8081 --workers 2 --forwarded-allow-ips '*' &
