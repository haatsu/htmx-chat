"""ローカル起動用(policy #18)。本番では使用しない(本番はgunicorn)。"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
