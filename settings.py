#put rq worker config details. otherwise, we need to pass redis url and queue name to the worker when we run the command in render.com

import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUES = ["emails", "default"]
