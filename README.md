# CryptoWorker

This project processes blockchain transactions using Web3. A simple Docker setup
is provided so the worker can run in a container.

## Building the image

```bash
docker build -t cryptoworker .
```

## Running

The application relies on several environment variables (database and Ethereum
connection details). Create a `.env` file or pass them directly when running the
container:

```bash
docker run --env-file .env cryptoworker
```

The container executes `python main.py` by default.
