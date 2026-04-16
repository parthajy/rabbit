# EMERGENCY SPRINT SYNC + PRODUCTION HOTFIX
**Company:** Apex Digital Solutions Inc. *(HQ: Austin, Texas)*
**Team:** Offshore Engineering Pod — India Delivery Team
**Meeting Type:** Emergency Sunday Sync *(originally unscheduled)*
**Date:** Sunday, February 23, 2025
**Time (US):** 10:14 AM CST — 1:52 PM CST
**Time (India):** 9:44 PM IST — 1:22 AM IST *(Monday, February 24)*
**Platform:** Zoom (Meeting ID: 847-391-2056)
**Note-taker:** Neha Iyer *(assigned at start of call)*

---

## ATTENDEES

### Apex Digital — United States
| Name | Role | Location |
|------|------|----------|
| **Brad Kowalski** | VP of Engineering | Austin, TX |
| **Stephanie Marsh** | Senior Product Manager | Denver, CO |
| **Jason Tate** | Senior Solutions Architect | Nashville, TN *(joined 11:02 AM CST)* |

### Apex Digital — India Offshore Team
| Name | Role | Location | Local Time at Join |
|------|------|----------|--------------------|
| **Arjun Mehta** | Tech Lead | Bengaluru | 9:44 PM IST |
| **Priya Krishnamurthy** | Senior Backend Developer | Pune | 9:44 PM IST |
| **Saurabh Joshi** | Frontend Developer | Hyderabad | 9:46 PM IST |
| **Divya Nair** | QA Engineer | Bengaluru | 9:44 PM IST |
| **Rahul Sharma** | DevOps Engineer | Noida | 9:51 PM IST |
| **Neha Iyer** | Junior Backend Developer | Bengaluru | 9:45 PM IST |

---

## PRE-MEETING CONTEXT *(compiled by Arjun Mehta, submitted with notes)*

At 7:18 PM IST on Sunday, February 23rd, Brad Kowalski sent a message in the #apex-india-dev Slack channel:

> *"Hey team — we've got a situation. The ClientConnect module pushed Friday night is throwing 500 errors on bulk CSV uploads for enterprise accounts. Kartik Mehta at FinVault (our biggest client) escalated this morning. Also, Stephanie needs the dashboard filter feature wrapped up before the Monday 9 AM stakeholder demo. Going to need everyone online for a few hours. Let's jump on a call at 10 AM CST. Sorry for the Sunday."*

The India team received this message between 7:18 PM and 7:45 PM IST. Divya Nair was at a cousin's engagement function in Bengaluru. Saurabh Joshi was in Hyderabad visiting his parents for the first time in four months. Rahul Sharma had just sat down for Sunday dinner with his family in Noida. Priya Krishnamurthy was available and had, in her words, "already been expecting something like this."

This is the third consecutive Sunday the India team has been called in for unscheduled work in February 2025.

---

## TRANSCRIPT

---

**BRAD KOWALSKI:** Hey, hey — good morning everyone. Or good evening, I guess, for the India crew. Sorry about this, truly. I know it's Sunday night over there and I wouldn't be doing this if it wasn't serious. Can everyone hear me okay?

**ARJUN MEHTA:** Yes, Brad, we can hear you. Good morning.

**BRAD KOWALSKI:** Great. So, let me just — Stephanie, you want to give the overview or should I?

**STEPHANIE MARSH:** Go ahead, I'll add context after.

**BRAD KOWALSKI:** Okay. So, two things today. First and most urgent — the ClientConnect bulk upload bug. FinVault is our second-largest enterprise account, $180,000 ARR, and they can't upload their client CSV files as of Saturday morning. Their admin team works weekends, apparently, and they hit this yesterday and escalated to our account manager. Kartik's team sent over a stack trace. I'm going to paste it in the chat right now. Second thing — Stephanie's stakeholder demo is Monday 9 AM CST with the Prentice Group. The dashboard filter needs to be functional. Saurabh, I know you were working on that last week.

**SAURABH JOSHI:** Yes, Brad, the filter is about 90% done. I need to finish the date range picker and the export button.

**BRAD KOWALSKI:** Great, great. So — if we can get the hotfix out and the filter done today, we're in great shape for tomorrow. Arjun, can you take point?

**ARJUN MEHTA:** Yes. Let me look at the stack trace first. *(pause)* Okay, I can see it in the chat. Can you scroll down? I want to see the full trace.

**BRAD KOWALSKI:** Yeah hold on. *(typing)* Okay, I've pasted the full thing.

**ARJUN MEHTA:** *(reading)* Okay. It's a null pointer in the CSV parser. Line 847 of the BulkUploadService. It's failing when the CSV has more than 500 rows and one of the header columns is — okay, I see it. It's the optional `account_region` column. If that column is missing in the CSV, the parser throws a null reference instead of using a default value. This is a known issue we discussed in sprint planning in January. The fix was deprioritized.

**BRAD KOWALSKI:** Wait — it was deprioritized? When?

**ARJUN MEHTA:** January 14th sprint planning. Priya flagged it. I have the Jira ticket — APEX-1147. It was moved to the backlog because Stephanie said the enterprise CSV template always includes that column.

**STEPHANIE MARSH:** I said the template we provide always includes it. I didn't say client CSV files would always have it.

**PRIYA KRISHNAMURTHY:** Right. And that's exactly what I said in the sprint planning — that clients might upload their own CSV format and not our template. The risk was noted and the ticket was moved out of the sprint.

**STEPHANIE MARSH:** *(pause)* Okay. In hindsight that call was wrong. We should have kept it in. Let's not spend time on who said what — let's just fix it.

**ARJUN MEHTA:** Agree. Priya, you know this code. How long?

**PRIYA KRISHNAMURTHY:** The fix itself is fifteen minutes. But testing it end-to-end — validating with different CSV formats, making sure we haven't broken anything else in the parser — that's minimum two hours. And then deployment.

**BRAD KOWALSKI:** Is two hours necessary or can we do a quick smoke test and push?

**PRIYA KRISHNAMURTHY:** Brad, this is a bulk upload service. If we push a bad fix and it corrupts data imports for other clients, we have a much bigger problem than FinVault's CSV issue.

**BRAD KOWALSKI:** Fair point. Fair point. Okay, two hours. Divya, can you run QA on this?

**DIVYA NAIR:** Yes. But I need the fix first, I need a test environment that works, and I need Rahul to make sure the staging environment actually matches production. Last Friday's deployment had a config mismatch that wasted three hours of testing.

**RAHUL SHARMA:** *(typing in background)* I just joined. Sorry, I was — yeah, I'm here. Divya, what config mismatch? I didn't hear about this.

**DIVYA NAIR:** The environment variable for the file upload size limit was 5MB on staging and 25MB on production. So the tests I ran on Friday were not representative.

**RAHUL SHARMA:** That shouldn't have happened. Who changed the production config?

**PRIYA KRISHNAMURTHY:** It was set during the Friday deployment. I think the deploy script didn't carry over the updated .env file.

**RAHUL SHARMA:** Okay. I can check this and align the environments. Give me twenty minutes.

**BRAD KOWALSKI:** Twenty minutes to just align the environments?

**RAHUL SHARMA:** Brad, the environments are running on separate AWS instances. I need to SSH in, compare the config files, pull the correct values, restart the services, verify. Twenty minutes is actually fast.

**BRAD KOWALSKI:** Okay. Go. Priya, while Rahul is doing that, can you start the fix?

**PRIYA KRISHNAMURTHY:** I'll start writing the fix now. But I need to ask — what is the expected behavior when the `account_region` column is missing? Should it default to null, to a string "UNKNOWN," or should it throw a validation error back to the user?

**BRAD KOWALSKI:** What do you think?

**PRIYA KRISHNAMURTHY:** I think a validation error back to the user is cleanest — tell them which column is missing, let them fix their CSV. But that requires a change to the error messaging layer as well, which adds an hour.

**STEPHANIE MARSH:** We can't add an hour. Just default it to null and we'll document it.

**PRIYA KRISHNAMURTHY:** If we default to null, the analytics dashboard will show blank account_region for any client who uploads their own CSV format. That will confuse support teams.

**ARJUN MEHTA:** Stephanie, I agree with Priya. The validation error is the right call technically. I think we should do it properly.

**STEPHANIE MARSH:** And I understand that, Arjun, but we have a stakeholder demo in less than twenty-four hours and we have a client who can't use the product right now. The null default gets FinVault unblocked today. We fix the error messaging in the next sprint cleanly.

**ARJUN MEHTA:** *(pause)* Okay. Noted. Priya, null default for now. Log it. APEX-1147 stays open, I'll add a comment.

**PRIYA KRISHNAMURTHY:** Fine. I'll document my objection in the ticket as well.

**BRAD KOWALSKI:** Great. Thank you, both. Now — Saurabh. The dashboard filter. Walk me through where you are.

**SAURABH JOSHI:** Sure. The filter component itself is working. Category filter, status filter, user filter — all functional. The date range picker I was building uses a library called react-datepicker and I ran into a timezone rendering issue on Friday. The dates display correctly for US users but for any account flagged as non-US, the dates shift by one day backward. I spent Friday afternoon on it and I have a workaround but it's not clean.

**STEPHANIE MARSH:** The Prentice Group is based in Chicago. Their demo account is US-based. Will the timezone issue affect their demo tomorrow?

**SAURABH JOSHI:** No. US accounts render correctly. The issue is only for non-US accounts.

**STEPHANIE MARSH:** Then can we just — get through the demo, and fix the timezone thing later?

**SAURABH JOSHI:** From a demo perspective, yes. From a code perspective, I'm not comfortable shipping known broken behavior. But yes, the Prentice demo will look fine.

**BRAD KOWALSKI:** Saurabh, I appreciate your diligence. Let's get through the demo and we'll address timezone as tech debt. What else do you need for today?

**SAURABH JOSHI:** The export button. When users filter and click export, it should download the filtered data as CSV. The backend endpoint for that — Priya, is it ready?

**PRIYA KRISHNAMURTHY:** The export endpoint exists. It's APEX-1203. But it doesn't filter — it exports everything. The filter parameters aren't being passed to the export query.

**SAURABH JOSHI:** How long to fix that?

**PRIYA KRISHNAMURTHY:** Priya already has her hands full with the hotfix. Honestly — an hour, maybe ninety minutes. But I need to finish the bulk upload fix first.

**ARJUN MEHTA:** Brad, to be transparent — Priya is now on two things simultaneously. The hotfix and the export endpoint. We are one senior backend developer doing two tasks. Neha can help but she's junior and the export endpoint has some complexity.

**BRAD KOWALSKI:** Can Neha do it with guidance?

**NEHA IYER:** I — I can look at it. I'd need Priya to walk me through the filter query structure first.

**PRIYA KRISHNAMURTHY:** I can explain it. It'll take thirty minutes to explain plus Neha's implementation time. Realistically Neha would finish the endpoint by midnight IST, maybe 12:30.

**BRAD KOWALSKI:** That's fine. That's 7 PM my time. More than enough for the demo.

**ARJUN MEHTA:** Brad — just to be clear about the timeline. We're at 10 PM India time right now. Midnight for Neha means she's working until midnight. That's Sunday night into Monday morning.

**BRAD KOWALSKI:** Right. I really do appreciate it, everyone. I know it's —

**ARJUN MEHTA:** I know you appreciate it. I just want to make sure the timeline is visible.

**BRAD KOWALSKI:** Completely fair.

*[Notification sound. Brad's video freezes briefly.]*

**BRAD KOWALSKI:** Sorry, Jason just messaged me. He's going to join in a few minutes — he has some thoughts on the ClientConnect architecture that might be relevant.

**ARJUN MEHTA:** Okay.

*[Approximately nine minutes of working silence. Priya and Rahul visible on camera, typing. Saurabh has his camera off. Divya is reviewing test cases.]*

---

### 11:02 AM CST — JASON TATE JOINS

**JASON TATE:** Hey folks, good Sunday morning. Arjun, Brad was telling me about the bulk upload issue. I actually have some context on the CSV parser — I was the one who originally wrote that service about eighteen months ago. The null handling issue you're describing, I think I know what's going on.

**ARJUN MEHTA:** Hi Jason. Yes, Priya is already writing the fix. Line 847, the optional column check.

**JASON TATE:** Right, but — okay, so the issue is bigger than that one line. The reason it fails on over 500 rows is that the parser is loading the entire CSV into memory before it validates. For small files it's fine. For 500+ rows it hits a memory threshold and the null check fails because the object state is partially initialized. If you just patch line 847, it'll work for the specific column issue but you're going to hit a different failure for large files with different missing columns.

**PRIYA KRISHNAMURTHY:** Jason — I've looked at the parser. I think you're describing the v1 implementation. The parser was refactored in November 2024. It's streaming now, not loading into memory.

**JASON TATE:** It was refactored?

**PRIYA KRISHNAMURTHY:** Yes. APEX-889. Sprint 14. I was one of the engineers on that refactor.

**JASON TATE:** *(pause)* Okay. I hadn't seen that. So the memory issue is resolved.

**PRIYA KRISHNAMURTHY:** Yes. The current issue is purely the null check on the optional column. The fix I'm writing is correct.

**JASON TATE:** Great. Then I'm — yeah, you're good. Carry on. Sorry for the noise.

**ARJUN MEHTA:** No problem. Good to double-check.

**BRAD KOWALSKI:** Jason, while you're on — Stephanie has the stakeholder demo tomorrow. Any architecture concerns about the dashboard filter before it ships?

**JASON TATE:** I mean, I haven't reviewed the code. Saurabh, you built it?

**SAURABH JOSHI:** *(camera back on)* Yes.

**JASON TATE:** What state management are you using for the filters?

**SAURABH JOSHI:** React context with useReducer.

**JASON TATE:** And how many filter combinations are there?

**SAURABH JOSHI:** Currently four filter types — category, status, user, date range. Each with multiple values. So potentially 16 to 20 combinations in the worst case.

**JASON TATE:** Does it rerender the full table on every filter change or are you debouncing?

**SAURABH JOSHI:** Debouncing with a 300 millisecond delay and memoizing the filter results. The table only rerenders when the filtered dataset changes.

**JASON TATE:** Good. What's the largest dataset the Prentice demo account has?

**STEPHANIE MARSH:** Their demo account has about 400 records loaded.

**JASON TATE:** Should be fine then. I'd be more worried on production with thousands of records but for a demo environment, 400 rows with debouncing is no issue.

**SAURABH JOSHI:** I've already tested with 1,000 records locally. It holds up. The virtualized list handles it.

**JASON TATE:** You're using virtualization. Nice. I'm satisfied. I'll leave you to it.

---

### 11:31 AM CST — ENVIRONMENT ALIGNMENT ISSUE

**RAHUL SHARMA:** Okay everyone — I've got an update on the staging environment. And I need to say this clearly because it affects our timeline. The staging environment is not just missing the file size config — it's running a different version of the application than production. The deploy from Friday deployed to production successfully but the staging branch has a four-commit lag. When Divya runs her QA tests on staging, she's not testing what's on production.

**BRAD KOWALSKI:** How does that happen?

**RAHUL SHARMA:** The CI/CD pipeline has two triggers — a production trigger that runs on merge to main, and a staging trigger that runs on merge to the staging branch. The developer who pushed the Friday fix merged to main but didn't merge to staging. So production moved forward, staging didn't.

**BRAD KOWALSKI:** Who pushed the Friday fix?

**ARJUN MEHTA:** I need to check the git log. *(typing)* It was me. I was under pressure to get the Friday fix out before EOD US time. I pushed to main, deployed, verified on production, and did not update staging because by that point it was 11:30 PM IST on Friday and I was tired.

**BRAD KOWALSKI:** Okay.

**ARJUN MEHTA:** I should have done it. But it was midnight and I had been online since 7 AM.

**BRAD KOWALSKI:** I hear you.

**RAHUL SHARMA:** It will take me forty-five minutes to sync the environments. Not twenty minutes like I said earlier. I have to cherry-pick the Friday commits onto the staging branch, run the pipeline, verify the config parity, and make sure there are no merge conflicts.

**DIVYA NAIR:** Which means I cannot start QA until 12:15, maybe 12:30 CST.

**BRAD KOWALSKI:** That pushes everything. If Divya can't start QA until 12:30, when are we looking at a production deployment?

**DIVYA NAIR:** The hotfix itself — if Priya's fix is clean and the test cases pass on the first run — two hours of QA minimum. So 2:30 CST at best.

**BRAD KOWALSKI:** 2:30. That's 1 AM India time.

**DIVYA NAIR:** Yes.

**BRAD KOWALSKI:** I'm going to be straight with everyone. 2:30 CST on a Sunday is going to be a problem for me personally because I have a thing at 3. But the more important question is — is 2:30 too late to help FinVault today? Stephanie, do FinVault's admins work Sunday afternoons?

**STEPHANIE MARSH:** I'll message Kartik now. *(typing)* Their SLA is 24 hours for critical issues. The issue was reported Saturday morning CST. So technically we have until Sunday morning CST to be within SLA, which means we're already outside SLA.

**BRAD KOWALSKI:** So we're already late on SLA regardless of what we do today.

**STEPHANIE MARSH:** Yes. But getting them a fix today is better than Monday. Kartik said his team needs to run their monthly client report on Monday morning and they need the bulk upload to work.

**BRAD KOWALSKI:** Right. Okay. Then we push for 2:30. Arjun, can the team sustain through 2:30 CST — which is what, 1 AM India?

**ARJUN MEHTA:** *(pause — long pause)* Brad. I want to answer this honestly. This is the third Sunday in February we have been called into an emergency meeting. Two weeks ago it was the payment gateway issue. Last Sunday it was the report generation bug. Today it's this. Every Sunday. And today, multiple people on this team had personal plans — Divya was at a family function, Saurabh was visiting his parents who he hadn't seen since October. I'm not saying we won't do it. I'm saying I think it's important for you to hear what this looks like from our side.

*[Silence. Brad's background — a quiet, sunlit home office — is visible on screen. He is sitting comfortably in a t-shirt.]*

**BRAD KOWALSKI:** Arjun. You're right. And I'm not going to be defensive about it. This has become a pattern and it shouldn't have. The right fix is better process — better testing before Friday deployments, staging environment parity maintained automatically, a proper on-call rotation with compensation. None of those things exist right now and that's a leadership failure, not a team failure. I hear you.

**ARJUN MEHTA:** Thank you for saying that.

**PRIYA KRISHNAMURTHY:** Can I add something? The Friday deployment — the reason I was pushing to get it done before US end-of-day on Friday is because the Friday sync always ends with "can we get this deployed today so it's live for the weekend?" I have seen that pattern every week for six months. Every Friday, something must go out before 6 PM CST. That means 11:30 PM IST for us. And then when that rushed deployment breaks something over the weekend, we come back in on Sunday to fix it.

**BRAD KOWALSKI:** That's a real observation. The Friday push culture — I know it exists. I've contributed to it. Stephanie, I think we need to have a real conversation about deployment windows.

**STEPHANIE MARSH:** I agree. Monday through Thursday deployments make more sense. But that's a conversation for a working day. Right now we have a client issue.

**ARJUN MEHTA:** We know. We will fix it. I just want the Monday through Thursday deployment conversation to actually happen, not to be deferred indefinitely.

**BRAD KOWALSKI:** I will put it on the agenda for Wednesday's eng sync. That is a commitment.

**ARJUN MEHTA:** Thank you. Priya, how is the fix?

**PRIYA KRISHNAMURTHY:** I'm done writing it. It's seven lines of code. I'm running it locally now.

---

### 12:07 PM CST — HOTFIX REVIEW AND UNEXPECTED COMPLICATION

**PRIYA KRISHNAMURTHY:** Arjun, can you review my fix before I send it to Divya?

**ARJUN MEHTA:** Yes. *(screen share begins)* Okay. I see the change. You've added a null check for `account_region` and defaulting to null string. You've also added a — wait. What's this condition on line 849?

**PRIYA KRISHNAMURTHY:** I noticed that the parser also has the same issue with the `account_type` column, which is also optional. I fixed both while I was there.

**ARJUN MEHTA:** Okay but `account_type` is not the reported issue. If we change two things and something breaks in QA, we won't know which change caused it.

**PRIYA KRISHNAMURTHY:** That's true. But if I leave the `account_type` issue and it surfaces next week—

**ARJUN MEHTA:** Next week we will fix it in a planned sprint. Let's revert the `account_type` change for now. Keep this hotfix surgical.

**PRIYA KRISHNAMURTHY:** Fine. Reverting now.

**JASON TATE:** Priya, I want to just say — the instinct to fix both was correct engineering. Arjun's call to keep the hotfix minimal is also correct. These two things are not contradictory. You're both right for different reasons.

**PRIYA KRISHNAMURTHY:** *(quietly)* Thank you, Jason.

**ARJUN MEHTA:** Agreed. Priya, once reverted, push to a branch and open a PR. I'll do a quick review and merge. Rahul, how close are you on the environments?

**RAHUL SHARMA:** Fifteen more minutes. The pipeline ran but one of the config values I pulled from production is an encrypted secret and I can't directly copy it to staging. I need to pull the plaintext value from the secrets manager. Give me fifteen minutes.

**NEHA IYER:** Priya, can we do the export endpoint walkthrough while you're waiting?

**PRIYA KRISHNAMURTHY:** Yes. Let me share my screen. So the export endpoint is in `ReportController.java`, line 234. The current implementation calls `reportService.exportAll()` which ignores any filter parameters. What you need to do is pass the `FilterDTO` object from the request into `exportAll()` and then modify the service method to build a conditional query based on which filters are populated.

**NEHA IYER:** Okay. What's the filter DTO look like?

**PRIYA KRISHNAMURTHY:** It's already defined — `DashboardFilterDTO`. It has five fields: category, status, userId, dateFrom, dateTo. All optional. If a field is null, the query should not filter on that dimension.

**NEHA IYER:** So I'm building a dynamic query?

**PRIYA KRISHNAMURTHY:** Yes. JPA Specifications is the cleanest way. Have you used that?

**NEHA IYER:** I've seen it but never written one.

**PRIYA KRISHNAMURTHY:** Okay. I'll write the Specification class — it's boilerplate — and you write the service layer that calls it. That way you're doing the parts you understand and I'm writing the part that's tricky. We work faster together than if I explain everything first.

**NEHA IYER:** That works for me.

**BRAD KOWALSKI:** I love the teamwork. Saurabh, while we're waiting on environments — how's the date range picker?

**SAURABH JOSHI:** I'm working on it right now. The component is rendering. The issue I hit is that the Prentice demo account has data going back to 2022 and when a user selects a date range that spans across years, the calendar UI flickers. It's a CSS transition issue — I can suppress the transition and it looks fine.

**STEPHANIE MARSH:** Will the Prentice people notice?

**SAURABH JOSHI:** If they specifically try to select a three-year range during the demo, possibly. But I can configure the demo to only show 2024 data in the filter, which eliminates the scenario entirely.

**STEPHANIE MARSH:** Then let's do that. Configure the demo to 2024 data and we remove the flickering risk entirely.

**SAURABH JOSHI:** I'll send you the updated demo URL by 7 PM CST.

**STEPHANIE MARSH:** By 7 PM — that's what time for you?

**SAURABH JOSHI:** 5:30 AM Monday morning IST.

**STEPHANIE MARSH:** Oh — Saurabh, you don't need to wait up that long. As long as I have it before 8:30 AM CST, I'm fine for a 9 AM demo.

**SAURABH JOSHI:** 8:30 CST is 7 PM IST. I'll have it done by 6 PM IST. I'd rather get it done tonight and sleep.

**STEPHANIE MARSH:** Are you sure?

**SAURABH JOSHI:** Stephanie, I appreciate you asking. But if I don't finish it tonight I'll be anxious about it and won't sleep well anyway. I'll finish it.

---

### 12:44 PM CST — QA BEGINS, THEN FAILS

**RAHUL SHARMA:** Environments are synced. Divya, you're good to go. I've confirmed config parity — all environment variables match between staging and production. I've also set up a separate upload test folder in S3 with sample CSV files — small file, medium file, 500-row file, 600-row file, one with the `account_region` column, one without it, one with a blank `account_region` value.

**DIVYA NAIR:** Thank you, Rahul. Starting test run now.

*[Seven minutes of mostly quiet. Keyboard sounds. Brad appears to be working on something else.]*

**DIVYA NAIR:** Okay. First result. Small file, all columns present — upload succeeds. Correct. Small file, `account_region` missing — upload succeeds, `account_region` defaults to null. Correct. 500-row file, `account_region` missing — upload succeeds. Correct. 600-row file, `account_region` missing —

*[Pause.]*

**DIVYA NAIR:** It's failing.

**ARJUN MEHTA:** What?

**DIVYA NAIR:** 600-row file, missing `account_region`, upload fails with a different error. Not the original 500 error — it's a timeout. The response is 408.

**PRIYA KRISHNAMURTHY:** A 408 is a request timeout. That's not a parser error. That's the upload taking too long.

**ARJUN MEHTA:** How long is it taking?

**DIVYA NAIR:** The request is sitting open for about 31 seconds and then the gateway cuts it off.

**RAHUL SHARMA:** That's the API gateway timeout. It's set to 30 seconds on our load balancer.

**PRIYA KRISHNAMURTHY:** Why is a 600-row CSV taking 30 seconds to process?

**ARJUN MEHTA:** It shouldn't. A 600-row CSV is not a large file. Rahul, what's the file size?

**RAHUL SHARMA:** *(checking)* 87 kilobytes.

**PRIYA KRISHNAMURTHY:** 87KB should process in under two seconds. Something is wrong. Let me look at the logs.

**BRAD KOWALSKI:** Jason, you still on?

**JASON TATE:** Yeah, I'm here. What are the logs showing?

**PRIYA KRISHNAMURTHY:** I'm looking now. The upload service is receiving the file. It's calling the parser. The parser is — wait. The parser is calling an external validation service. Why is it calling an external service?

**ARJUN MEHTA:** What external service?

**PRIYA KRISHNAMURTHY:** There's a call in the parser to the `AccountValidationService` microservice. It's running on port 8085. For each row, it's making an HTTP call to validate the account_id against the accounts database. For 600 rows, that's 600 HTTP calls.

**JASON TATE:** Oh no.

**ARJUN MEHTA:** Jason.

**JASON TATE:** That was in the v1 design. The per-row validation was supposed to be replaced by a bulk validation call in the refactor. Was it not replaced?

**PRIYA KRISHNAMURTHY:** I'm looking at the November refactor code now. The streaming was refactored. The per-row validation was not. It was left in.

**JASON TATE:** So the streaming processes rows efficiently but then hits the network for every single row individually.

**PRIYA KRISHNAMURTHY:** Yes. For 100 rows, it completes in under 5 seconds. For 600 rows, it hits the timeout.

*[Long silence.]*

**ARJUN MEHTA:** So the original bug report from FinVault — it's not the null check causing their failure. Or not only that. Their CSVs are large — probably several hundred to thousands of rows — and they're timing out.

**PRIYA KRISHNAMURTHY:** The null check fix I wrote is still correct. It prevents a different class of failure. But it doesn't solve FinVault's actual problem, which is the timeout.

**BRAD KOWALSKI:** How long to fix the bulk validation?

**JASON TATE:** *(slowly)* This is not a small fix. To replace per-row validation with bulk validation, you need to batch the account IDs, send them in a single request to the validation service, and handle the response mapping back to the original rows. The validation service itself may not support bulk input — I don't know what its current API looks like.

**PRIYA KRISHNAMURTHY:** It doesn't. I just checked. The `AccountValidationService` only has a single-record endpoint.

**BRAD KOWALSKI:** So we need to update the validation service too.

**PRIYA KRISHNAMURTHY:** Or we bypass the per-row validation for uploads above a certain row count and validate asynchronously after import. The data is stored either way — we just flag the rows that fail validation later.

**ARJUN MEHTA:** That is actually a better UX for users. Instead of a timeout that tells them nothing, they get an immediate success response and then notifications if any rows have validation issues.

**JASON TATE:** The async approach is architecturally cleaner too. But it requires a job queue, a status endpoint, and notifications. That's not today's work.

**BRAD KOWALSKI:** What can we do today?

*[Silence. The question hangs on the call.]*

**PRIYA KRISHNAMURTHY:** Today — realistically — we can do one thing. Increase the API gateway timeout from 30 seconds to 90 seconds. That buys FinVault enough headroom to get their files through for now. It is not a fix — it is a band-aid. But it will unblock FinVault for their Monday report.

**RAHUL SHARMA:** That's a config change on the load balancer. I can do it in five minutes.

**ARJUN MEHTA:** Brad. My recommendation is this. Today we do two things. One: increase the gateway timeout to unblock FinVault. Two: deploy Priya's null check fix which prevents the other class of failure. These are both applied to production today. Tomorrow — in a proper sprint planning session, during working hours — we scope the async bulk validation properly and build it correctly. It should take three to four days with two developers.

**BRAD KOWALSKI:** Will FinVault be satisfied with the timeout increase?

**STEPHANIE MARSH:** I'll contact Kartik and explain we've identified the root cause and implemented an interim fix, with a proper solution coming this week. That's a manageable conversation.

**BRAD KOWALSKI:** Okay. Do it. Rahul, make the timeout config change. Priya, proceed with your null check fix. Divya, please test both changes together on staging before anything goes to production.

**DIVYA NAIR:** Understood.

---

### 1:19 PM CST — PRODUCTION DEPLOYMENT

**RAHUL SHARMA:** Timeout config change is live on staging. Updated to 90 seconds.

**DIVYA NAIR:** Testing now with the 600-row file. *(forty-second pause)* Upload successful. Completed in 44 seconds. Within the 90-second window.

**DIVYA NAIR:** Running the null check test cases. *(two-minute pause)* All passing. Small file, missing column — success. Medium file, missing column — success. 600-row file, missing column — success.

**DIVYA NAIR:** I'm going to run one more scenario that wasn't in the original test plan. What happens when the CSV is malformed — not just missing a column but has inconsistent row lengths?

**ARJUN MEHTA:** Good catch. Run it.

**DIVYA NAIR:** *(four-minute pause)* It fails with a 400 bad request and a readable error message. That's correct behavior.

**ARJUN MEHTA:** Good. Divya, please sign off on QA and post your test results in the deployment ticket.

**DIVYA NAIR:** Done. Signed off.

**ARJUN MEHTA:** Rahul, ready to deploy to production?

**RAHUL SHARMA:** Ready. I have the deployment runbook open. Doing pre-deployment checks now. *(typing)* Production health check — green. Database connection pool — nominal. Memory usage — 34%. CPU — 12%. All good. Starting deployment.

*[Three-minute silence. Brad is visible on camera, watching.]*

**RAHUL SHARMA:** Deployment complete. Running post-deployment smoke test. *(ninety-second pause)* ClientConnect bulk upload — testing with production credentials and a 600-row file. *(forty seconds)* Upload successful. Post-deployment smoke test — passed.

**BRAD KOWALSKI:** We're live?

**RAHUL SHARMA:** We're live.

**BRAD KOWALSKI:** *(exhales)* Thank you. Genuinely. All of you.

---

### 1:38 PM CST — CLOSING

**STEPHANIE MARSH:** I've sent Kartik the message. He's responded already — he says "thank you, my team will test first thing Monday and I appreciate the quick turnaround." Quote-unquote. So we're in good standing with FinVault.

**BRAD KOWALSKI:** Great. Okay. I want to take a few minutes to close this out properly because I don't want to just say thank you and hang up. Arjun, you said something earlier that I want to address seriously. Three Sundays. You're right. That's three Sundays of emergency work in February alone. I made a commitment about the deployment window conversation on Wednesday and I want to extend that: I'm going to put together a formal on-call proposal by next Friday — February 28th — that includes weekend on-call compensation for whoever is on rotation. Not just "thank you for being available" — actual compensation. Rotational, not everyone every week. And I want the India team's input before I finalize it. Arjun, will you gather the team's thoughts and send me a summary by Tuesday?

**ARJUN MEHTA:** I will do that. Thank you, Brad. That means a lot to hear.

**BRAD KOWALSKI:** Priya — the fact that you flagged APEX-1147 in January and were overruled, and then it became a client escalation in February — that should be uncomfortable for us on the US side, not for you. The sprint planning process needs to give more weight to technical risk flags from engineers. I'm going to speak to Stephanie about formalizing a "risk hold" mechanism where any engineer-flagged risk requires explicit sign-off to deprioritize, not just a verbal "move it to backlog." Stephanie, are you okay with that?

**STEPHANIE MARSH:** Yes. I think that's reasonable. It should have happened with APEX-1147.

**PRIYA KRISHNAMURTHY:** I appreciate that. For the record — I'm not trying to be difficult when I raise these things. I just see what's going to break before it breaks.

**BRAD KOWALSKI:** That's your job and you're good at it. Please keep doing it.

**DIVYA NAIR:** Can I say something?

**BRAD KOWALSKI:** Please.

**DIVYA NAIR:** The staging environment parity issue — this has happened before. Not just today. In November, in December, in January. The CI/CD pipeline needs a mandatory staging merge requirement before production. If you cannot merge to production without also merging to staging, this class of problem disappears entirely. Rahul, is that technically feasible?

**RAHUL SHARMA:** Yes. It's a GitHub branch protection rule. I can configure it in twenty minutes. But it requires everyone to change their deployment habit — you have to merge to staging first, then to main.

**ARJUN MEHTA:** That's a small habit change for a big reliability gain.

**BRAD KOWALSKI:** Rahul, implement it. This week, not someday. Wednesday sync — I want to see it done and I want you to demo the new pipeline flow for ten minutes.

**RAHUL SHARMA:** Done.

**BRAD KOWALSKI:** Neha — how's the export endpoint?

**NEHA IYER:** Done. The Specification class Priya wrote is integrated. I've tested with three filter combinations — all returning correctly filtered data in the CSV download. Saurabh, you should be able to wire the frontend button to the updated endpoint now.

**SAURABH JOSHI:** I'll do it now. Should take twenty minutes.

**BRAD KOWALSKI:** Perfect. Saurabh, Neha — today was your first time working that closely together?

**SAURABH JOSHI:** Yes.

**BRAD KOWALSKI:** It should happen more often than an emergency Sunday call. I want cross-team pairing to be a regular thing, not crisis-driven. Arjun, add it to the Wednesday agenda.

**ARJUN MEHTA:** Will do.

**BRAD KOWALSKI:** One last thing. I know Jason dropped off — he had to jump to something — but the conversation about the async bulk validation. That work is going into the sprint. Priya, Arjun — I want a proper ticket scoped by Tuesday. Properly sized. Not rushed, not squeezed into something else. It's a real feature that deserves real planning time.

**ARJUN MEHTA:** Agreed. Priya and I will have the ticket written with acceptance criteria and an estimate by Tuesday COB India time — which is Tuesday morning CST.

**BRAD KOWALSKI:** Perfect. Alright. I think we're done. I'm going to say something that I mean seriously — I know you all gave up parts of your Sunday evenings and nights for this. That's not something I take lightly. The work you did today kept a $180,000 ARR client in good standing and set Stephanie up for a clean demo tomorrow. That matters. But the fact that it had to happen this way is on me and on the process, not on you. Let's fix the process so we're not here again in two weeks.

**ARJUN MEHTA:** Thank you, Brad. We'll get the Wednesday items ready.

**SAURABH JOSHI:** I'm going to finish the date range config and send Stephanie the demo URL.

**STEPHANIE MARSH:** Thank you, Saurabh. Really. Good luck with the rest of your evening.

**SAURABH JOSHI:** *(flatly, but not unkindly)* It's 1 AM.

**STEPHANIE MARSH:** *(pause)* I'm sorry.

**SAURABH JOSHI:** It's okay, Stephanie. Good luck with the demo.

*[Call ends: 1:52 PM CST / 1:22 AM IST — Monday, February 24, 2025]*

---

## POST-MEETING NOTE — ARJUN MEHTA *(submitted 1:31 AM IST)*

> *Everything is resolved for tonight. FinVault is unblocked. Dashboard filter is ready for the demo. Saurabh sent the demo URL at 1:28 AM. Neha's export endpoint is merged. Rahul has confirmed production is stable — no errors in the logs since deployment.*
>
> *Brad was more receptive tonight than I expected. I want to believe the on-call compensation and deployment window conversations will happen. I have been in enough of these calls to know that good intentions expressed on Sunday nights sometimes evaporate by Tuesday. We will see.*
>
> *For the record: Divya got home from the engagement function at 7 PM, logged in at 9:44 PM, and finished QA sign-off at 1:17 AM. She did not complain once.*

---

## ACTION ITEMS

| # | Owner | Action | Deadline |
|---|-------|--------|----------|
| 1 | Rahul Sharma | Configure mandatory staging-before-production pipeline rule in GitHub | **Wednesday, Feb 26 — demo at eng sync** |
| 2 | Arjun Mehta | Gather India team input on on-call structure and send to Brad | **Tuesday, Feb 25** |
| 3 | Brad Kowalski | Draft formal on-call rotation + weekend compensation proposal | **Friday, Feb 28** |
| 4 | Brad Kowalski | Add deployment window policy to Wednesday eng sync agenda | **Wednesday, Feb 26** |
| 5 | Priya + Arjun | Write APEX ticket for async bulk validation (async job queue + status endpoint) with full ACs and estimate | **Tuesday COB IST (Tuesday AM CST)** |
| 6 | Stephanie Marsh | Formalize "risk hold" mechanism for engineer-flagged sprint risks | **Wednesday eng sync** |
| 7 | Saurabh Joshi | Merge export button to updated filter endpoint; send demo URL to Stephanie | **Done (1:28 AM IST)** |
| 8 | Brad Kowalski | Schedule regular Saurabh + Neha cross-team pairing sessions | **Wednesday eng sync** |
| 9 | Rahul Sharma + Arjun | Demo updated CI/CD pipeline at Wednesday eng sync | **Wednesday, Feb 26** |
| 10 | Stephanie Marsh | Communicate interim fix status to Kartik at FinVault; set expectation on permanent fix timeline | **Done (1:41 PM CST Sunday)** |

---

## ISSUES LOG

| Issue | Root Cause | Resolution | Permanent Fix |
|-------|-----------|------------|---------------|
| Bulk CSV upload 500 error | Null reference on optional `account_region` column | Null check added, default to null | Done (deployed 1:19 PM CST) |
| Bulk upload 408 timeout for 600+ rows | Per-row HTTP calls to AccountValidationService (legacy from v1) | API gateway timeout increased 30s → 90s | Async bulk validation — scoped for next sprint |
| Staging env 4 commits behind production | Friday deploy merged to main only, not staging | Envs manually synced by Rahul | Mandatory staging-first pipeline rule (Rahul, Wed) |
| Dashboard filter date range flicker | CSS transition on multi-year range select | Demo scoped to 2024 data only | Tech debt ticket — next sprint |
| Dashboard export not filtering | Filter params not passed to export query | JPA Specification class added (Priya + Neha) | Done (merged 1:27 AM IST) |

---

*Notes compiled by: Neha Iyer | Reviewed by: Arjun Mehta*
*Distribution: Meeting attendees | CC: Brad Kowalski (action tracking)*
*Next scheduled interaction: Wednesday Engineering Sync — February 26, 2025, 10:00 AM CST / 9:30 PM IST*
