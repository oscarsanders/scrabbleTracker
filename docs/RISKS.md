# Risk register

P = probability, I = impact (L/M/H).

| ID | Risk | P | I | Mitigation / trigger |
|---|---|---|---|---|
| R-01 | **Gradio API drift** between minor versions (v6 already changed `theme`/`css`/`api_name`). | M | M | Bounded `<7.0`; UI smoke test; review Dependabot PRs; ADR-0002. |
| R-02 | **A game is lost** on reload, tab close, redeploy, restart, or when the free Render instance sleeps after ~15 min without traffic. | H | M | By design (ADR-0005). Keep the page active during a game; persistence is the next feature (ADR-0003). |
| R-03 | **Runtime behaviour of the UI handlers was not executed by the author** (no Gradio in the authoring environment). The domain, rendering and presentation logic (69 tests) were executed; the Gradio wiring was reviewed and its construction verified only against a stub. | M | M | Run the manual smoke test below on Render/locally and report any problem. |
| R-04 | Anyone with the URL can use the app and consume free-tier resources. | M | L | Acceptable for a trial; add authentication (ADR-0004) before sharing widely. |
| R-05 | Spanish tile table lacks the `RR` digraph. Verify against the official Spanish set before relying on it. | M | L | Add to `tiles.py` with a test once confirmed. |
| R-06 | No dependency lock file; builds are not bit-for-bit reproducible. | M | L | Generate one with `uv pip compile` or `pip-compile` and install from it. |

## Manual smoke test (R-03)

1. Open the app. Enter `Ana, Luis`, keep Spanish, press **Start game**.
2. Add a word move for Ana (e.g. `CASA`, 20), a scrabble for Luis (68), a foul
   with 15 points (it must show 0), a pass. Scores update after each.
3. Press **Undo player's last move** for Luis; his score drops.
4. Open **Finish game**, leave Ana's box empty, type `AE` for Luis, press
   **Close game and show ranking**. Ana gets +2, Luis −2, ranking shown 1–2 with a Winner badge, and the move form disappears.
5. Try adding a move now: it must be refused ("already finished").
6. **Start a new game** returns to the setup screen. Try a solo game (`Ana`).
7. Open the app in a second browser: it must show no game (isolation).
8. Switch the browser/OS to dark mode: names, table text and headers inside the cream cards stay dark and readable.
9. On a phone-width window the form and the move list stack; on a wide window they sit side by side.
