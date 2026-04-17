Chrome DevTools HAR capture flow — bytefight API recording
=========================================================

1. Open https://bytefight.org/compete/cs3600_sp2026 in Chrome (make sure you're logged in).
2. Open DevTools: F12 or Ctrl+Shift+I.
3. Click the "Network" tab.
4. Check "Preserve log" (checkbox near top).
5. Click the trash-can icon (clear button) to purge existing captures.
6. Perform THIS entire flow without page-navigating via the URL bar:
   a. Navigate to Team page.
   b. Click Submit Bot. Drag in any zip file (use a tiny throwaway — even a zip containing just an empty agent.py is fine; we don't care if validation fails, we just need the upload traffic).
   c. Wait for validation to complete (or fail — doesn't matter).
   d. Click "Set as Current" on any row (toggle back and forth if easier).
   e. Click a scrimmage crossed-swords icon on any reference bot from the Leaderboard. Submit the scrimmage.
   f. Go back to Team page. Watch for the match-status row to update (may need to refresh).
   g. Click on any completed match row to see if "Replay" or log data loads.
   h. Navigate to /submissions to see the full list.
7. In DevTools, right-click any request in the Network panel -> "Save all as HAR with content" -> save as `bytefight_capture_<YYYYMMDD>.har` to your Desktop or the repo's `tools/scratch/` folder.
8. Let me know the path when done — ping team-lead with the file location.

Important:
- Don't paste HAR content into chat (too big, possibly has auth tokens).
- After capture, LOG OUT of bytefight and LOG BACK IN if you're worried about leaked tokens (they'll rotate).
- The HAR may contain your auth cookies / JWT — treat it as sensitive. When we're done building the client we'll gitignore tools/scratch/*.har to make sure it doesn't end up on origin.
