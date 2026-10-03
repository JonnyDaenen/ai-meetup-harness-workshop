# 00: Setup check

Goal: one message goes from J5 through the proxy to the model and back.

1. Follow the [quickstart](../../README.md#quickstart-about-10-minutes): model running, proxy running, `.env` copied.
2. Run the vanilla agent:
   ```bash
   uv run --project agent python agent/j5_00_vanilla.py
   ```
3. Type `hi`. You should get a short, SMS-style answer signed "- J5".
4. Open <http://127.0.0.1:8081> and click the `POST /v1/messages` request.
5. Type `q` to quit, and read the token and cost summary.

✅ Done when you see your `hi` in the request body in mitmweb and the answer in the response.

Not working? See [troubleshooting](../../README.md#troubleshooting).
