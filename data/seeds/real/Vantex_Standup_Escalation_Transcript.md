# TEAM STANDUP — ENGINEERING & PRODUCT DELIVERY
**Team:** Platform Delivery Squad — Vantex Systems Ltd.
**Meeting Type:** Daily Standup *(escalated mid-session)*
**Date:** Wednesday, March 12, 2025
**Time:** 9:03 AM – 11:41 AM WAT
**Location:** Open-plan meeting pod, Floor 3, Vantex Systems HQ, Abuja
**Facilitator:** Nnamdi Eze, Engineering Manager
**Note-taker:** Amara Chukwu, Delivery Lead *(asked to start taking notes at 9:31 AM when meeting escalated)*

---

## TEAM MEMBERS PRESENT

| Name | Role |
|------|-------|
| **Nnamdi Eze** | Engineering Manager |
| **Amara Chukwu** | Delivery Lead / Scrum Master |
| **Roland Okafor** | Senior Backend Engineer |
| **Damilola Adisa** | Frontend Engineer |
| **Chidera Nwoke** | Frontend Engineer |
| **Tunde Bello** | QA Engineer |
| **Fatou Diallo** | Junior Backend Engineer |
| **Zainab Musa** | Product Analyst |

**Joined at 9:31 AM (escalation):**
| **Chiamaka Obi** | HR Business Partner |

**Joined remotely at 9:38 AM:**
| **Victor Salami** | Head of Product *(Lagos, remote via Teams)* |

---

## PRE-MEETING CONTEXT *(Amara Chukwu, compiled post-meeting)*

This standup was originally scheduled as a routine 30-minute daily sync. It became something else within the first fifteen minutes. The team has been running a critical client delivery — the Remitech Payments API integration — since January 6, 2025. Original go-live date was February 14th. It was pushed to February 28th. Then to March 7th. As of this morning, March 12th, the integration is still not live. The client — Remitech — sent a formal breach-of-SLA letter to Vantex's commercial team on March 10th. Nnamdi received an email from Victor Salami at 7:44 AM this morning asking him to "get to the bottom of this today." Chiamaka Obi from HR was notified separately by Victor the previous evening.

Nobody on the team, except possibly Nnamdi, knew this morning that HR was going to walk into the standup.

---

## TRANSCRIPT

---

**NNAMDI EZE:** Alright, let's go. Nine o'three, everyone's here. Quick standup — what did you do yesterday, what are you doing today, any blockers. Roland, start us off.

**ROLAND OKAFOR:** Yeah. Yesterday I was finishing the webhook retry logic. The retry mechanism is working — tested it locally, it handles failure states correctly. Today I'm integrating it with Tunde's test environment so he can run the full regression. Blockers — none right now, but I need Tunde to give me access to the staging environment because my credentials expired last Friday and the IT ticket I raised is still open.

**TUNDE BELLO:** The staging environment is ready. I'll sort your credentials this morning — I can escalate the IT ticket with Ovie directly.

**ROLAND OKAFOR:** Please do. That's been sitting for four days.

**NNAMDI EZE:** Four days for a credential issue? Tunde, why is that only being escalated now?

**TUNDE BELLO:** I didn't know Roland's credentials had expired until yesterday. He didn't mention it in Monday's standup.

**ROLAND OKAFOR:** I mentioned it in the Slack channel on Friday.

**NNAMDI EZE:** The Slack channel is not the standup. If there's a blocker, it goes in the standup. Both of you — that's a communication gap. Tunde, escalate the IT ticket immediately after this meeting. Not this afternoon. Immediately. Damilola, go.

**DAMILOLA ADISA:** Yesterday I was on the UI — specifically the transaction status screen. The design was updated by Zainab on Monday and I was implementing the changes. I finished the status screen. Today I'm moving to the payment confirmation modal. Blockers — the design for the confirmation modal hasn't been finalized. I have a draft but Zainab flagged three changes on Tuesday afternoon and I'm waiting for the final version before I build it.

**ZAINAB MUSA:** I sent the final version last night. 8:47 PM. It's in Figma and I linked it in the project Notion page.

**DAMILOLA ADISA:** I haven't seen it. I stop checking Slack after 7 PM.

**NNAMDI EZE:** *[pause]* Damilola. We are twelve days past the client deadline. I need you to check Slack after 7 PM right now. I'm not saying this should be permanent. I'm saying this is a delivery crisis and we are all making adjustments. The design is in Figma. You have no blockers. Chidera, go.

**CHIDERA NWOKE:** Yesterday — I was on the KYC form integration. The form is pulling user data from the API correctly. The issue I hit is that the KYC validation rules are different from what's in the technical spec. The spec says date of birth should be validated as DD/MM/YYYY, but the backend is returning MM/DD/YYYY. So my form is rejecting valid dates. I raised it with Roland yesterday afternoon.

**ROLAND OKAFOR:** I saw that. The date format is what Remitech sent us in their API documentation. If their documentation is wrong, that's their issue, not ours.

**CHIDERA NWOKE:** Except it's blocking my form from working.

**NNAMDI EZE:** Roland, is this a one-line fix on the backend?

**ROLAND OKAFOR:** Probably. Twenty minutes.

**NNAMDI EZE:** Then fix it. Don't debate whose documentation is correct. Fix it and document the discrepancy for the post-mortem. Chidera, today?

**CHIDERA NWOKE:** Once Roland fixes the date issue, I'm finishing the validation logic and moving to the terms and conditions acceptance flow. Should be done by end of day.

**NNAMDI EZE:** Should be, or will be?

**CHIDERA NWOKE:** Should be. There's a dependency on the backend terms endpoint that Fatou is building.

**NNAMDI EZE:** Fatou, status on the terms endpoint.

**FATOU DIALLO:** I finished the endpoint yesterday. It's deployed to staging. Chidera can use it.

**CHIDERA NWOKE:** Oh — I didn't see that update.

**NNAMDI EZE:** Again — communication. Is the endpoint documented?

**FATOU DIALLO:** I added it to the API doc sheet this morning.

**NNAMDI EZE:** Good. Chidera, you have no blockers. "Will be done by end of day" is now the answer. Say it.

**CHIDERA NWOKE:** *(quietly)* Will be done by end of day.

**NNAMDI EZE:** Thank you. Fatou, continue.

**FATOU DIALLO:** Yesterday — terms endpoint, done. Today — I'm working on the session timeout handler. When a user's payment session expires, the error message currently shows a raw JSON error, not a user-facing message. I need to intercept that and return a readable string. It's a small task. I expect it done by noon. Blockers — none.

**NNAMDI EZE:** Good. Zainab, design and product analysis side.

**ZAINAB MUSA:** Yesterday I finalized the confirmation modal design, did a review of the end-to-end user flow with Amara, and drafted the UAT checklist. Today I'm finishing the UAT checklist — it has about 40 test scenarios — and I need to walk Tunde through it so QA knows what we're testing. Blockers — I've been waiting for Victor to confirm whether the Remitech client wants the transaction receipt to include a reference number in QR format or just plain text. I sent that question to Victor on March 6th. I have not gotten a response.

**NNAMDI EZE:** March 6th. Today is March 12th. Six days.

**ZAINAB MUSA:** Yes.

**NNAMDI EZE:** I'll escalate to Victor directly. Amara, delivery status overall.

**AMARA CHUKWU:** I'll be honest, Nnamdi — the delivery status is not where it should be. Based on what I'm hearing this morning, the core integration — webhook, KYC, session management — is 80 to 85% complete. QA regression hasn't started because Roland's environment access is blocked. UAT hasn't been scheduled because the product spec has an open question. We are realistically looking at a March 17th readiness for QA entry, and March 21st for UAT. Client go-live — if everything goes well in UAT — March 24th or 25th.

**NNAMDI EZE:** The client sent a breach letter on Monday. Their expectation, as of this morning, is go-live by Friday.

*[Silence around the pod.]*

**ROLAND OKAFOR:** Friday as in — this Friday? March 14th?

**NNAMDI EZE:** That's what the breach letter implies.

**ROLAND OKAFOR:** That's not possible. Not without cutting corners that will break things post-launch.

**TUNDE BELLO:** I haven't even started regression. I can't run a full regression in two days.

**NNAMDI EZE:** I know. I need everyone to understand the severity of the situation, because I don't think it has been fully felt in this team. We are five weeks past the original deadline. Every week of delay costs Vantex a penalty clause. And this morning—

*[Door to the meeting pod opens. Chiamaka Obi from HR steps in.]*

---

### 9:31 AM — HR JOINS THE MEETING

**CHIAMAKA OBI (HR):** Good morning, everyone. I'm sorry to interrupt. Nnamdi, Victor asked me to join this session. Do you want me to wait or—

**NNAMDI EZE:** No, please come in. Everyone, this is Chiamaka Obi, HR Business Partner. Chiamaka, you can take the seat next to Amara.

*[The team exchanges glances. Fatou looks at her laptop screen. Chidera picks up a pen and puts it down.]*

**CHIAMAKA OBI:** Thank you. I just need a few minutes with the team — we can continue the standup after. Or we can integrate it, whatever works.

**NNAMDI EZE:** Let's give Chiamaka the floor.

**CHIAMAKA OBI:** Thank you, Nnamdi. Good morning, everyone. I'll be direct because I think you deserve directness. I was asked to join this meeting because Vantex's commercial team has received a client breach letter. HR's role in that isn't to discipline — it's to understand whether there are people factors contributing to the delivery challenges, and to make sure the team has the support it needs. But I also need to be honest: where individual performance is a contributing factor, that has to be addressed.

*[Teams notification sound. Nnamdi checks his phone.]*

**NNAMDI EZE:** Victor has joined on Teams. Let me put him on the screen. *[Laptop is shared to the wall display.]* Victor, can you hear us?

**VICTOR SALAMI (remote, Head of Product):** Yes, I can hear you. Good morning, everyone. Chiamaka, thank you for being there. I'm going to listen, but I want to say one thing to the team before Chiamaka continues. I spoke with the Remitech account director, Emeka Obi, at 8 AM this morning. They have given us until March 21st as an absolute final date. Not March 24th, not March 25th. March 21st. If we are not live by March 21st, they are exercising their right to terminate the contract and seek a replacement vendor. That contract is worth ₦47 million annually. I need everyone in that room to hold that number.

*[Long pause.]*

**ROLAND OKAFOR:** *(quietly, to no one in particular)* March 21st. That's nine days.

**VICTOR SALAMI:** Roland, I heard that. Nine days. Yes. I believe it's achievable if we work differently than we have been. Chiamaka, please continue.

**CHIAMAKA OBI:** Thank you, Victor. So — I've reviewed the delivery timeline for this project. What I want to do is ask some questions, and I want honest answers. The first question is: when did the team first know that the February 14th deadline was not going to be met?

*[Silence. Eight seconds.]*

**AMARA CHUKWU:** I knew by January 31st that we were behind. I raised it in the weekly delivery report on February 3rd.

**CHIAMAKA OBI:** Nnamdi, did you receive the February 3rd delivery report?

**NNAMDI EZE:** Yes.

**CHIAMAKA OBI:** And when did you escalate to Victor?

**NNAMDI EZE:** *[pause]* February 10th.

**CHIAMAKA OBI:** So there was a seven-day gap between the delivery lead flagging a concern and the engineering manager escalating it.

**NNAMDI EZE:** I wanted to assess whether the team could self-correct before pulling Victor in. I thought we had a path.

**CHIAMAKA OBI:** I'm not challenging that judgment right now. I'm establishing the timeline. So February 14th deadline is missed. The date moves to February 28th. Who approved that extension?

**VICTOR SALAMI:** I approved it. I informed the client.

**CHIAMAKA OBI:** And by February 28th, what was the status?

**AMARA CHUKWU:** We were at approximately 60% completion on February 28th.

**CHIDERA NWOKE:** I was still getting spec changes on February 26th. The KYC requirements changed—

**CHIAMAKA OBI:** I'll come to spec changes in a moment. I want to understand the 60% figure first. Nnamdi, on February 28th, the team was 60% complete. The deadline was that day. What happened?

**NNAMDI EZE:** We pushed again to March 7th. I informed Victor and he informed the client.

**VICTOR SALAMI:** And I want to be clear — informing the client of a second delay was an extremely difficult conversation. Remitech did not respond well. They gave us March 7th as a final deadline at that point. And then March 7th passed.

**CHIAMAKA OBI:** Right. So three missed deadlines. February 14th, February 28th, March 7th. And we are now on March 12th. What I need to understand — and I need individual honesty here, not team-level answers — is what each person's contribution to this delay looks like. I'm going to ask each of you. Not to embarrass anyone. But because I need to separate systemic issues from individual performance issues, and those require different responses.

**ROLAND OKAFOR:** I have a problem with this framing. We're five weeks behind, and some of that is my code and some of it is spec changes that happened after the sprint was locked. On February 10th, the Remitech API documentation changed — they added a two-factor authentication requirement that wasn't in the original scope. That added at least two weeks of backend work that was not in my original estimate. I documented it. Amara has it.

**AMARA CHUKWU:** That's accurate. The 2FA addition was out of scope. I logged it as a scope change on February 11th.

**CHIAMAKA OBI:** Victor, was the scope change formally logged and communicated to the client?

**VICTOR SALAMI:** It was communicated verbally. I don't have written documentation of the scope agreement.

**CHIAMAKA OBI:** That's a process gap we'll return to. Roland, I'm not disputing the scope change. What I'm asking is — excluding the scope change weeks — in the remaining timeline, were there areas where your output fell below what was expected?

**ROLAND OKAFOR:** *(long pause)* There were two weeks in February where I was dealing with a personal matter. My productivity was lower than usual. I should have communicated that more clearly.

**CHIAMAKA OBI:** Thank you for saying that. I'll come back to you privately. Damilola — you were asked to deliver the payment flow UI by February 21st. You delivered it on March 4th. That's eleven days late. Walk me through that.

**DAMILOLA ADISA:** The design kept changing. I can't build a screen that's being redesigned while I'm building it.

**ZAINAB MUSA:** The design changed twice — once on February 13th because the client sent new brand guidelines, and once on February 24th because Victor requested the button placement change after the demo.

**VICTOR SALAMI:** That's fair. The February 24th change was my decision.

**CHIAMAKA OBI:** So one change was client-driven, one was internally driven. But Damilola — between January 6th and February 13th, before any design changes, the payment flow UI had six weeks of stable design. What was the delivery status at the end of those six weeks?

**DAMILOLA ADISA:** I was about 40% done.

**CHIAMAKA OBI:** Forty percent in six weeks. The expectation was 100% in four weeks. Even accounting for other tasks, that gap is significant. I want to have a separate conversation with you, Damilola.

**DAMILOLA ADISA:** *(quietly)* Okay.

**CHIAMAKA OBI:** Tunde — QA. You haven't started regression. The client deadline is March 21st. How much time do you need for a complete regression?

**TUNDE BELLO:** A thorough regression for a project this size is typically five to seven days. If I get build access today — which depends on Roland's credentials being sorted — I can start today. If I run lean — prioritizing the highest-risk flows — I can be done in four days. March 16th.

**CHIAMAKA OBI:** March 16th for regression sign-off. That leaves five days for UAT and go-live preparation. Victor, is that workable?

**VICTOR SALAMI:** It's tight. Remitech needs two business days for their own UAT. If Tunde signs off on March 16th, Remitech does their UAT March 17th and 18th. That leaves March 19th for fixes and March 20th for final deployment. March 21st go-live. It works on paper if nothing breaks in UAT.

**TUNDE BELLO:** Things always break in UAT.

**VICTOR SALAMI:** I know, Tunde. Let's hope they're small things.

---

### 10:19 AM — PIP DISCUSSION

**CHIAMAKA OBI:** I want to step back and address something directly, because I think avoiding it will only make the conversation harder. Based on the information I've reviewed — the delivery timeline, the team's standup logs, and the Jira ticket history that Nnamdi shared with me last night — there are two members of this team whose performance patterns over this project period have been a consistent contributing factor to the delays. I want to have that conversation now, in part because Victor is present, and in part because I think transparency — done with dignity — is better than people wondering what HR is here for.

The two people I'm referring to are Damilola Adisa and Chidera Nwoke. I want to be clear — a Performance Improvement Plan is not a termination notice. It is a structured, supported opportunity to meet the standards of the role. It comes with coaching, clear targets, and check-ins. But it is also a formal process, and it is in your personnel file, and I think you deserve to know that clearly and not in a softened way that leaves you confused about the seriousness.

*[The room is extremely quiet. Fatou has stopped typing. Zainab is looking at the table.]*

**DAMILOLA ADISA:** *(voice tight)* I want to understand what specifically I'm being put on a PIP for.

**CHIAMAKA OBI:** That's a fair question and you deserve a clear answer. Damilola, the PIP is being initiated on the basis of the following: delivery of assigned tasks at 40% completion rate after six weeks of stable scope; two previous one-on-one conversations with Nnamdi in December 2024 and January 2025 where performance concerns were raised; and a pattern of communication gaps — work not flagged as blocked, design dependencies not escalated, Slack updates going unchecked during critical delivery periods. None of these alone would trigger a PIP. Together, across this project, they represent a sustained performance gap.

**DAMILOLA ADISA:** The one-on-ones in December and January — I was told those were informal check-ins.

**NNAMDI EZE:** I used the word "informal" because I didn't want to alarm you before the pattern was clear. In hindsight, I should have been more direct about what those conversations meant.

**CHIAMAKA OBI:** Nnamdi, that's something we'll address in your manager development as well. Conversations where performance is being assessed need to be labeled clearly so that the team member understands what they're participating in. That's a management process issue on our side.

**DAMILOLA ADISA:** I appreciate you saying that.

**CHIAMAKA OBI:** Chidera — yours is different in texture. Your technical output has been largely on track. The issue that has been flagged is responsiveness and collaboration. You have raised three separate blockers in the last six weeks — the date format issue, the terms endpoint dependency, the design delay — and in each case, the blocker sat for more than 24 hours before it was surfaced in a standup or escalated. On February 19th, you were blocked for three days on a CSS rendering issue that Roland could have fixed in under an hour. Instead of raising it, you worked around it with a solution that has since caused a display bug in the payment status screen.

**CHIDERA NWOKE:** I didn't want to keep going to Roland for help. It felt like I was bothering him.

**ROLAND OKAFOR:** *(surprised)* Chidera, that's literally what I'm here for.

**CHIDERA NWOKE:** I know. I know that now.

**CHIAMAKA OBI:** Chidera, the PIP for you is focused on one thing: communication and escalation behavior. It is narrower than Damilola's. The targets will be specific — blockers escalated within four working hours, daily standup participation that is honest about status, and two weeks of pairing with Roland on complex frontend-backend interactions. If you meet those targets consistently for thirty days, the PIP is closed. It does not go to a formal warning. It closes.

**CHIDERA NWOKE:** *(nods. Does not speak.)*

**CHIAMAKA OBI:** I want to say to the whole team — the rest of you are not in this process. That doesn't mean everything is fine for everyone. What it means is that what I've seen in the rest of the team is people working under a system that has not supported them well. Spec changes without formal sign-off. Credential issues that sit for four days. Escalation delays. Those are not individual failures — those are team and process failures, and they belong to all of us including management. We're going to fix those. But I need the two of you — Damilola and Chidera — to understand that your patterns predate the system failures, and that's what makes it an individual conversation.

**VICTOR SALAMI:** *(from the screen)* Chiamaka, I want to say something to the whole team. Whatever happens in the HR process, everyone in that room has nine days to deliver something that matters enormously to this company. I don't want today's conversation to feel like an ambush that makes the next nine days impossible. Can we close the HR portion and go back to the delivery plan?

**CHIAMAKA OBI:** Yes. Damilola and Chidera — I'll schedule individual sessions with each of you this afternoon. The formal PIP documents will be ready by end of day Friday, March 14th. You'll each have five business days to review and respond before signing. The PIP period begins Monday, March 17th, and runs for thirty days. Nnamdi is your manager of record for the process and I am the HR contact. Any questions?

**DAMILOLA ADISA:** Do I have the right to bring someone to my individual session?

**CHIAMAKA OBI:** You can bring a colleague of your choice — not a direct manager. It is not a formal disciplinary hearing, so legal representation is not applicable at this stage.

**DAMILOLA ADISA:** Okay.

**CHIDERA NWOKE:** I don't have questions right now.

**CHIAMAKA OBI:** That's fine. I'll step back and let Nnamdi take the room. I'll stay in the building — I'm in the small conference room on this floor if anyone needs me. Nnamdi?

---

### 10:38 AM — DELIVERY PLANNING RESUMES

**NNAMDI EZE:** Thank you, Chiamaka. *(pause)* Okay. I know that was a lot. I want to give everyone sixty seconds. Get water, step out for a moment if you need to. Then we come back and we build the plan that gets us to March 21st. Because that is what we're doing today — we are not going home without a plan.

*[Break: 10:38 – 10:46 AM. Chidera steps out briefly. Damilola gets water. Roland and Tunde talk quietly near the window.]*

---

**NNAMDI EZE:** Alright. Everyone back. Victor, still with us?

**VICTOR SALAMI:** Still here.

**NNAMDI EZE:** Amara, let's build the nine-day delivery plan on the board. Call out what needs to happen and who owns it.

**AMARA CHUKWU:** Okay. Today, March 12th — three things must close. One: Roland fixes the date format issue in the KYC validator. Twenty minutes, he said. Two: Tunde gets Roland's staging credentials — Tunde, you said you'd handle that this morning. Three: Zainab finalizes the UAT checklist and walks Tunde through it by 3 PM today so QA is not waiting on documentation when the build is ready.

**ZAINAB MUSA:** Checklist will be done by 1 PM. Tunde, 2 PM walkthrough?

**TUNDE BELLO:** Works for me.

**AMARA CHUKWU:** Thursday, March 13th — Roland completes the webhook retry integration with Tunde's environment and does a smoke test. Chidera finishes the terms and conditions acceptance flow. Damilola completes the payment confirmation modal — the design is in Figma as of last night. Fatou finishes the session timeout handler by noon and writes the error message strings.

**FATOU DIALLO:** Session timeout is done by noon today actually. I said noon earlier. I'm ahead.

**AMARA CHUKWU:** Even better. Fatou, after the session timeout — can you pick up the API response logging? That's the last outstanding backend task.

**FATOU DIALLO:** Yes, I can take that.

**AMARA CHUKWU:** Friday, March 14th — Tunde begins full regression. Roland and Chidera are on standby for bug fixes — meaning they are not starting new tasks; they are available to fix anything QA surfaces within two hours. Nnamdi, I want to propose we have a 5 PM check-in on Friday to assess QA progress and recalibrate if needed.

**NNAMDI EZE:** Agreed. 5 PM Friday is a mandatory check-in. Attendance is not optional.

**AMARA CHUKWU:** Weekend — we may need to work Saturday if QA regression surfaces significant bugs. I know that's not comfortable. But March 21st doesn't move.

**ROLAND OKAFOR:** I'll be available Saturday.

**TUNDE BELLO:** Same.

**DAMILOLA ADISA:** I'll be available.

**CHIDERA NWOKE:** I'll be there.

**NNAMDI EZE:** Good. That's noted. March 17th, Monday — QA regression complete. Regression sign-off document sent to Victor by end of day. Remitech UAT access configured and handover email sent to their technical team.

**VICTOR SALAMI:** I'll send Remitech the UAT access instructions on Friday the 14th so they know it's coming. That gives them the weekend to prepare their test team.

**AMARA CHUKWU:** March 17th to 18th — Remitech UAT. We need someone from our team on standby during their UAT hours. Remitech is Lagos-based, so I'm assuming normal business hours.

**VICTOR SALAMI:** Their UAT lead is Kemi Adesola. She runs from 9 AM to 5 PM. I'll confirm.

**AMARA CHUKWU:** Nnamdi, I'd suggest Roland is on standby for Remitech's UAT — any backend issues that surface need same-day resolution.

**ROLAND OKAFOR:** Noted. I'll keep my calendar clear.

**AMARA CHUKWU:** March 19th — fix day. All UAT-identified bugs addressed. Final build cut by 6 PM. March 20th — deployment to production. Full deployment checklist run by Tunde and Roland. Rollback plan confirmed and documented. March 21st — go-live. Monitoring for 24 hours.

**VICTOR SALAMI:** That is a real plan. I want to say that. Amara, can you put this in writing and have it in my inbox by 4 PM today?

**AMARA CHUKWU:** Yes.

**VICTOR SALAMI:** And I need the open QR code question answered. Zainab, I apologize for not responding to your March 6th query. I'm going to call Kemi at Remitech right after this call. Expect an answer from me by noon today.

**ZAINAB MUSA:** Thank you.

**NNAMDI EZE:** Victor, one more thing. The verbal scope agreement on the 2FA addition — Amara's going to document that retrospectively with dates, the communication thread, and the estimated time impact. I want a written scope change acknowledgment from Remitech, even if it's informal, even if it's an email confirmation from Kemi. Can you get that?

**VICTOR SALAMI:** I'll add it to the Remitech call. Yes.

**NNAMDI EZE:** Good. This protects us if there's any commercial dispute about the penalty clauses.

---

### 11:14 AM — TEAM CONCERNS AND CLOSE

**NNAMDI EZE:** Before we close — I want to give the room space. We've covered a lot today. We had an HR conversation that was difficult. We have a hard deadline. I've been running this team for eight months and I know you're tired. I'm not going to tell you it's fine when it's not. The last five weeks have been a mess — there are things I should have caught earlier, there are escalation failures that I own, and there are process gaps that made your jobs harder than they needed to be. I'm not asking you to work the next nine days for the company's bottom line. I'm asking you to do it because you are capable of it and because the version of this project that ships on March 21st is something you'll be able to point to. What questions do you have for me?

**FATOU DIALLO:** I want to ask something. Not to be difficult — genuinely. The PIP process for Dami and Chidera starts on March 17th. That's the same week as Remitech's UAT. That's a lot of pressure on two people at the same time.

**NNAMDI EZE:** Fatou, that's a fair observation. Chiamaka?

**CHIAMAKA OBI:** *(from the doorway — she has been listening)* I've heard that. The PIP periods will begin March 17th as stated, but the formal check-in conversations — where targets are being assessed — will not happen until the week of March 24th. So in practical terms, Damilola and Chidera have the next nine days to focus on delivery. The PIP is a backdrop, not an active pressure during the UAT period.

**DAMILOLA ADISA:** I appreciate that. Thank you.

**TUNDE BELLO:** I have a technical question. If Remitech's UAT identifies more than fifteen bugs — which is possible, it's a payment integration — the March 19th fix day is not enough. What's the contingency?

**NNAMDI EZE:** If we hit a bug count that blows the timeline, I call Victor immediately. We do not silently absorb the slippage. We have an honest conversation with Remitech on March 18th if necessary. Victor, agreed?

**VICTOR SALAMI:** Agreed. But Tunde, I'd ask you to also triage hard. Not every UAT bug is a launch blocker. Severity 1 and 2 items block go-live. Severity 3 and below go on a post-launch patch plan. Teach Kemi's team that framework so they're not flagging cosmetic issues as showstoppers.

**TUNDE BELLO:** I'll set that expectation with them.

**ROLAND OKAFOR:** One thing I want to say and then I'm done. I've been on this project since day one. The problems we've had are real and some of them are mine. The credential thing — I should have raised it louder and faster. The two weeks in February where I was slower — I should have said something. I didn't because I didn't want to look like I couldn't handle the workload. I've learned something today about what happens when you don't say anything. So I'm saying something now: I will do what it takes to ship this by March 21st. I'll be in early, I'll fix bugs same-day, and I'll be honest if I'm blocked.

*[Brief silence.]*

**NNAMDI EZE:** Thank you, Roland. That means a lot. Alright — let's close the meeting. Here is what leaves this room.

Roland: Fix the date format issue right now. Literally in the next thirty minutes.

Tunde: Escalate Roland's IT credentials and do not leave that task to someone else.

Damilola: The confirmation modal is your entire world today. Nothing else.

Chidera: Terms and conditions flow, done by end of day. No exceptions.

Fatou: Session timeout done by noon, then API response logging.

Zainab: UAT checklist to Tunde by 1 PM. QR code question answered by Victor by noon.

Amara: Nine-day delivery plan document to Victor by 4 PM.

Me: I will be in this office until the work is done. You will not be chasing me.

Victor: Remitech call, scope change acknowledgment, QR answer by noon. March 21st go-live target confirmed.

Chiamaka: Individual sessions with Damilola and Chidera this afternoon. PIP documents ready by Friday.

We meet again at 5 PM today — brief check-in, fifteen minutes — to confirm morning blockers are resolved. We do not skip it. We do not postpone it. See you at 5.

*[Meeting ended: 11:41 AM WAT]*

---

## ACTION ITEMS

| # | Owner | Action | Deadline |
|---|-------|--------|----------|
| 1 | Roland Okafor | Fix KYC date format (DD/MM vs MM/DD) | **By 10:30 AM, March 12** |
| 2 | Tunde Bello | Escalate Roland's staging credentials with IT | **By 10:30 AM, March 12** |
| 3 | Zainab Musa | Finalize UAT checklist (40 test scenarios) | **1 PM, March 12** |
| 4 | Zainab Musa + Tunde Bello | UAT checklist walkthrough | **2 PM, March 12** |
| 5 | Fatou Diallo | Session timeout handler complete | **Noon, March 12** |
| 6 | Fatou Diallo | API response logging | **March 13** |
| 7 | Damilola Adisa | Payment confirmation modal (complete) | **EOD March 12** |
| 8 | Chidera Nwoke | Terms and conditions acceptance flow | **EOD March 12** |
| 9 | Amara Chukwu | Nine-day delivery plan document sent to Victor | **4 PM, March 12** |
| 10 | Victor Salami | Call Remitech; QR code question answered | **Noon, March 12** |
| 11 | Victor Salami | Obtain written scope acknowledgment for 2FA addition | **March 14** |
| 12 | Nnamdi Eze + team | Mandatory 5 PM check-in | **5 PM, March 12** |
| 13 | Tunde Bello | Begin full QA regression | **March 14** |
| 14 | Tunde Bello | QA regression sign-off, sent to Victor | **EOD March 17** |
| 15 | Chiamaka Obi | Individual PIP sessions with Damilola + Chidera | **Afternoon, March 12** |
| 16 | Chiamaka Obi | PIP documents ready for review | **EOD March 14** |

---

## PIP SUMMARY *(HR Record — Confidential)*

| Employee | PIP Start | PIP Duration | Key Focus Areas | Review Date |
|----------|-----------|--------------|-----------------|-------------|
| Damilola Adisa | March 17, 2025 | 30 days | Delivery pace, communication, proactive escalation | April 16, 2025 |
| Chidera Nwoke | March 17, 2025 | 30 days | Blocker escalation (within 4hrs), standup transparency, pairing practice | April 16, 2025 |

*PIP documents to be reviewed and signed within 5 business days of issuance (deadline: March 19, 2025). HR contact: Chiamaka Obi. Manager of record: Nnamdi Eze.*

---

## DELIVERY PLAN SUMMARY (MARCH 12–21, 2025)

| Date | Milestone | Owner |
|------|-----------|-------|
| March 12 | KYC fix, credentials, modal, T&C flow, UAT checklist | Full team |
| March 13 | Webhook integration, smoke test, backend logging | Roland, Fatou |
| March 14 | QA regression begins; 5 PM leadership check-in; PIP documents issued | Tunde + all |
| March 15–16 | QA regression continues; weekend standby if needed | Tunde, Roland |
| March 17 | QA regression sign-off; Remitech UAT access configured | Tunde, Nnamdi |
| March 17–18 | Remitech UAT (Kemi Adesola's team); Roland on standby | Roland, Victor |
| March 19 | UAT bug fixes; final build cut by 6 PM | Roland, Chidera, Damilola |
| March 20 | Production deployment; rollback plan confirmed | Roland, Tunde |
| **March 21** | **Go-live. 24-hour monitoring begins.** | **Full team** |

---

*Notes compiled by: Amara Chukwu, Delivery Lead | Reviewed by: Nnamdi Eze*
*Distribution: Meeting attendees + Victor Salami + HR file (PIP section: restricted)*
