# 01: Inspect traffic and tokens

Goal: know exactly what an LLM call contains and what it costs. No coding yet.

## Part A: J5's traffic

Run `agent/maxi/j5_00_vanilla.py` with the proxy open, and have a short conversation of three or four turns.

1. **Open one `POST /v1/messages` request.** Find `model`, `system`, `messages` and `max_tokens`. What is in `tools`?
2. **Open the response.** Find `content`, `stop_reason` and `usage`. Which fields tell you the cost?
3. **Count the requests.** How many requests does one turn make? You should see more than one. Find out which line in `j5_00_vanilla.py` causes the extra ones. *Hint: look at `calculate_tokens` and where it's called. When does Python evaluate the arguments of `log.debug(...)`?*
4. **Watch the history.** Compare `messages` in turn 1 and turn 4. The model is stateless: what does that mean for the size of each request?
5. **Fill in this table** from `usage` in the proxy:

   | Turn | input_tokens | output_tokens |
   |---|---|---|
   | 1 | | |
   | 2 | | |
   | 3 | | |

   Why does `input_tokens` grow even if your messages are short?
6. **Check J5's bookkeeping.** Quit with `q`. Does the summary match your table? Compare with the logs in `.j5/history/`.

## Part B: a production harness

Open the samples in [`proxy/captures/`](../../proxy/captures/) (or capture your own; see [docs/claude-code.md](../../docs/claude-code.md)).

1. `01_session_title.json`: which model is this, and what is it asked to do? Why would a harness make a call you never see?
2. `02_first_turn.json`: the user typed `hi!`. Roughly how many tokens is the rest? (About 4 characters per token is a fair estimate.)
3. Find the `<system-reminder>` blocks. Who wrote them: the user, the model or the harness?
4. Find `cache_control`. What problem does it solve, given what you saw in Part A, step 4?
5. `03_tool_call.json`: find the `tool_use` block and its matching `tool_result`. How are they linked?

## Part C (if you have time): local vs remote

Ask both paths the same question. Compare the latency, `usage`, and how long each answer is. What changes in the request? What changes in the response?

## Takeaways

- An LLM call is stateless. The harness resends the entire conversation every time.
- Most input tokens are the harness's own: the system prompt, tool definitions and reminders. Your message is a small part.
- Cost and latency grow with the size of the context, not with your message.
