# Diagnose the failing layer

Read `troubleshooting.md` in the documentation directory identified by `SKILL.md`. Use its symptom tables and current workarounds. Identify the exercise, process, attempted operation, redacted error, and timestamp; ask only for missing evidence.

Run preflight for local configuration, then inspect the relevant evidence: Keycard Activity for credential requests, Expense Desk for business refusals, or Temporal history and worker logs for recovery. If no connected browser or API is available, guide the attendee through their own view. Local file checks can't verify live registration.

Apply the smallest repair supported by the evidence. Restart the affected process after `.env` edits and retry the original operation once. If it still fails, investigate the new evidence rather than repeating the same fix. Keep expected exercise refusals intact and route shared-service changes to the instructor.

## Instructor handoff

Prepare a redacted summary of the exercise, operation, environment, timestamp, error, failing resource, relevant event or workflow ID, and checks performed. Identify the shared setting that needs inspection and distinguish hypotheses from confirmed causes. Let the attendee share the summary unless they authorize you to send it.

For checkpoint recovery, follow the exercise guide and preserve local edits before restoring code. If time runs short, use the instructor's paired demonstration and save unresolved work for take-home recovery.

## Activity or creation controls unavailable

In this workshop, missing Activity access or application/resource creation controls can mean you still have the Viewer role. Ask the instructor to grant Admin access, then refresh the console. Don't modify another attendee's registration to work around missing permissions.
