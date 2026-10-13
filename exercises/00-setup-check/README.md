# 00: Setup check

Goal: one message goes from J5 through the proxy to the model and back.

1. Follow the [quickstart](../../README.md#quickstart-about-10-minutes): model running, proxy running, `.env` copied.
2. Run the vanilla agent:
   ```bash
   uv run --project agent python agent/maxi/j5_00_vanilla.py
   ```
3. Type `hi`. You should get a short, SMS-style answer signed "- J5".
4. Open the call viewer at <http://127.0.0.1:8082> and click the newest call. (The full mitmweb UI is at <http://127.0.0.1:8081>.)
5. Type `q` to quit, and read the token and cost summary.

✅ Done when you see your `hi` in the call viewer, and the answer under Response.

Not working? See [troubleshooting](../../README.md#troubleshooting).
