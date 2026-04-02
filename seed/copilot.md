1. Ticket status updates







03/16/2026 -







Anjan shared a dashboard displaying all tickets closed or marked as resolved from 1st March to yesterday, covering the first two weeks of March.



Brian requested access to the dashboard query, and Anjan agreed to share it.



Anjan noted that some interface issue tickets, although actively worked on, were created before March and are not shown in the current dashboard.



Ticket resolution process







Anjan explained that tickets are marked as resolved only if created by their team, otherwise the user who created the ticket is assigned to validate and close it.



Anjan explained that tickets are marked as resolved only if created by their team; otherwise, the user who created the ticket is assigned to validate and close it.



Dashboard usage







Brian confirmed that the Argonal Managed Services dashboard with pie charts is used for executive-level reporting and monthly leadership meetings.



Ticket reporting







Brian requested that ticket metrics align with the consumption report period, covering all tickets worked on since the partnership began.



Misha confirmed that metrics on open and closed tickets can be provided, but tracking hours per case is not available.



Meeting processes







Misha and Brian discussed the process by which business unit managers gather and escalate updates from their teams for the Tuesday meeting, ensuring relevant issues are raised at the leadership level.



Feedback and improvement







Misha and Brian agreed to seek more quantitative feedback from teams to provide actionable insights for improvement.



Testing and environment management







Misha raised the recurring issue of pre-production environment configurations being wiped out during refreshes, and suggested discussing alternative approaches to avoid duplicated work in the upcoming Wednesday meeting.



Audit preparation







Anjan confirmed that the revision of user profiles for audit and licensing purposes is still in progress, with a target to complete before the 27th, ahead of the audit deadline.



Interface documentation







Anjan explained that some interface documentation provided was primarily designed for GPAC issues and not for D65, making it less relevant and requiring further review to identify useful information.



Consumption reporting







Misha presented new visual trends of weekly consumption hours and confirmed that higher consumption weeks were linked to interface issues.



Follow-up tasks







Task Assigned to Due date Bucket



Create ADA tickets to track unresolved issues such as the Azure BLOB storage problem (Anjan)



Compile open and closed ticket metrics since the start of the engagement to align with the consumption report and share with Brian (Misha, Anjan)



Begin tracking weekly consumption trends and provide visual estimates for review (Misha)



Review recent links and documents shared by Suzuki and Brian to identify relevant information for DDXT web purposes (Anjan)











9th mar 26











Production deployments







Anjan shared that several quick wins and managed services code fixes were recently deployed to production.



Anjan confirmed that the team has been prioritising interface issues, and several critical items were fixed and deployed in the last two production releases.



Issue management







The main focus of current work has been on resolving interface issues, alongside other open issues.



Brian confirmed that Julio and a representative from SISON will join tomorrow's meeting to help address interfacing errors



Reporting requirements







Brian highlighted the need to start reporting ticket status, including open and closed rates, in the weekly internal meetings.



The participants discussed providing a monthly snapshot of ticket closures and openings, with the option to filter weekly data as needed.



Ticket management







Brian relayed user feedback regarding the length of time tickets are taking to close, without citing specific examples.



Misha requested that, when receiving general feedback about ticket delays, the team should seek more detailed information to identify affected tickets.



Usage reporting







Anjan presented the latest weekly usage report, confirming that scheduled hours for the quarter have been completed.



Scope and ticket categorisation







The participants discussed that data sharing tasks related to Yanmar Holdings should be treated as a separate scope, outside of managed services, and considered how to tag these tickets appropriately.



Brian and Anjan discussed that tasks requiring over 10 hours of effort should be treated as separate engagements, not managed services, and communicated this to Bill and Suzuki



Ticket categorisation







The participants discussed the need to create a new tag for tickets related to tasks outside managed services, as current tags do not cover these items.



Scope clarification







Misha highlighted that the team must ensure all stakeholders are aware that work on these tasks cannot proceed without proper approval and scope definition.











2 mar 2026 -











Database refresh







Anjan confirmed that the prod database data refresh from production to pre-prod is pending Lisa's completion of 8739 testing



Deployment and permissions







Brian stated that permission issues remain unresolved for some Quick Win items deployed to pre-prod, despite partial fixes



Anjan informed that all Quick Win items deployed to pre-prod will be included in the production deployment planned for next Friday



Data push coordination







Brian confirmed that he followed up with the Japan team and copied Mr. Suzuki to arrange a meeting for planning the 2931 files data push, but has not yet received a response due to a holiday



Licensing and user access







Anjan reiterated that licensing changes based on Misha's suggestions will be implemented, and users may lose access to forms they no longer require; any concerns should be directed to the team



Quick Win deployment status







Brian stated that several Quick Win items are ready for review in pre-production, but permission issues delayed their deployment to production; the team aims to resolve these and provide a status update to leadership by the end of the month



Project planning and prioritisation







Brian clarified that phase two items, including new credit management tasks, will not be addressed until all open quick wins, both functional and reporting, are completed and closed out.



Brian emphasised the need to prevent any outstanding quick wins from overlapping with phase two planning to avoid confusion between project scopes.



Request management







Anjan stated that recent requests from the finance department, such as bulk invoice processing, have been categorised as tasks rather than support tickets and will be revisited in a future meeting.

2.
Product analytics and feature rollout

03/22/2026 -

Anjan shared a dashboard showing feature usage trends from March 5th to date, highlighting adoption across the first rollout cohort.

Brian asked for access to the underlying query and filters, and Anjan agreed to share them after the meeting.

Anjan noted that some legacy feature usage is missing, as those events were tracked before the new analytics pipeline went live.

Feature validation process

Anjan explained that a feature is marked as “validated” only when instrumented events match expected user flows; otherwise, product owners must verify discrepancies.

Anjan clarified that engineering-owned features follow automated validation, while externally requested features require manual confirmation.

Dashboard usage

Brian confirmed that the executive dashboard is used during monthly product reviews to assess adoption and drop-offs across key flows.

Reporting alignment

Brian requested that analytics reports align with the billing cycle, capturing all feature usage since the pricing model update.

Misha confirmed that usage counts and event frequency can be tracked, but session-level attribution is currently unavailable.

Meeting workflows

Misha and Brian discussed how product leads consolidate insights from their teams before the weekly roadmap sync, ensuring only high-impact updates are escalated.

Feedback and iteration

Misha and Brian agreed to introduce structured feedback collection from users to better prioritize feature improvements.

Infrastructure concerns

Misha raised concerns about analytics pipelines resetting during staging refreshes, suggesting a need for persistent tracking configurations.

Audit and compliance

Anjan confirmed that user activity logs required for compliance review are still being consolidated, targeting completion before the 30th.

Documentation gaps

Anjan noted that existing documentation focuses on legacy modules and is not fully applicable to the new feature set, requiring updates.

Usage trends

Misha presented weekly active user trends, noting spikes correlated with recent feature releases.

Follow-up tasks

Task | Assigned to | Due date | Bucket

Share analytics query and dashboard filters (Anjan)

Prepare aligned usage report based on billing cycle (Misha, Anjan)

Implement structured user feedback collection (Misha)

Review and update outdated product documentation (Anjan)

15th Mar 26
Feature releases

Anjan shared that multiple minor feature improvements were deployed to production over the past week.

Anjan confirmed that the team prioritized onboarding flow enhancements, with several fixes included in the latest release.

Issue tracking

The current focus remains on resolving inconsistencies in analytics tracking alongside minor UI issues.

Brian confirmed that external stakeholders will join upcoming discussions to review tracking discrepancies.

Reporting needs

Brian emphasized the need to include feature adoption metrics in weekly internal reviews.

The team discussed providing both weekly snapshots and monthly summaries for better visibility.

User feedback

Brian relayed general feedback about confusion in new features but did not specify exact cases.

Misha requested more detailed examples to isolate problem areas.

Usage tracking

Anjan presented updated usage metrics, confirming expected engagement levels for the current phase.

Scope definition

The team discussed that experimental features should be tracked separately from core product metrics.

Brian and Anjan agreed that features requiring significant effort should be treated as separate initiatives.

Categorization

The team identified the need for new tagging to differentiate experimental vs production features.

Scope communication

Misha emphasized ensuring stakeholders understand the distinction between experimental work and core roadmap items.

8 Mar 2026 -
Data pipeline updates

Anjan confirmed that migration to the new analytics system is pending final validation steps.

Deployment and access

Brian noted that access issues persist in staging dashboards despite partial fixes.

Anjan confirmed all pending updates will be included in the next production push.

Coordination

Brian mentioned delays in external data sync due to dependencies on another team’s schedule.

Access control

Anjan reiterated that access changes may restrict visibility for some users based on updated roles.

Release readiness

Brian stated that several features are ready but blocked due to unresolved tracking issues.

Roadmap prioritization

Brian clarified that new feature development will not proceed until current rollout issues are resolved.

Request handling

Anjan noted that certain internal requests are being treated as future enhancements rather than immediate priorities.

3.
Platform reliability and incident tracking

03/25/2026 -

Rohit shared a reliability dashboard covering incidents from March 10th to present, highlighting uptime fluctuations across core services.

Elena asked whether the dashboard includes degraded performance events or only full outages. Rohit clarified it primarily tracks incidents logged via PagerDuty, not silent degradations.

Karan pointed out that several latency spikes reported by customers are missing, as they were never formally logged as incidents.

Rohit acknowledged this gap and suggested integrating observability alerts into the reporting pipeline.

Incident classification

Rohit explained that incidents are classified as “resolved” only after root cause analysis (RCA) is completed and documented.

Elena disagreed slightly, noting that from a customer perspective, incidents are considered resolved once service is restored, regardless of RCA completion.

Karan added that internal dashboards still reflect incidents as “open” until RCA closure, creating discrepancies between internal and external reporting.

Dashboard consumption

Elena confirmed that leadership reviews the reliability dashboard weekly but relies more heavily on summarized SLA reports during board meetings.

Rohit mentioned that the current dashboard was not designed for SLA reporting, which explains inconsistencies in numbers shared externally.

Reporting inconsistencies

Karan highlighted that incident counts differ between the reliability dashboard and monthly reports shared with clients.

Rohit explained that monthly reports include manually added incidents that were missed in real-time tracking.

Elena suggested aligning both views, even if it requires backfilling data.

Escalation workflows

Elena described how team leads consolidate incident updates before escalation calls, often summarizing multiple related alerts into a single issue.

Karan noted that this aggregation sometimes hides the frequency of recurring problems.

Rohit suggested tagging related incidents instead of merging them.

Feedback loops

Elena emphasized the need for clearer post-incident feedback from customers, beyond generic satisfaction scores.

Karan proposed adding structured fields to capture impact severity and business disruption.

Environment instability

Rohit raised concerns that staging environments are frequently reset, causing loss of debugging context for ongoing issues.

Elena mentioned that similar concerns were raised last month but no changes were implemented.

Karan suggested maintaining snapshot logs before each reset.

Compliance and audit

Rohit confirmed that incident logs required for compliance audits are partially complete, with missing entries for early March.

Elena stressed the importance of completing logs before the audit review scheduled next week.

Documentation gaps

Karan noted that existing runbooks do not cover newer microservices introduced this quarter.

Rohit acknowledged this and said updates are pending but not prioritized.

Trend analysis

Elena presented a trend showing increased incidents correlated with recent infrastructure changes.

Rohit argued that correlation does not necessarily imply causation and suggested deeper analysis.

Follow-up tasks

Task | Assigned to | Due date | Bucket

Integrate observability alerts into incident dashboard (Rohit)

Align incident counts between dashboard and client reports (Elena, Rohit)

Define structured customer feedback fields (Karan)

Update runbooks for new microservices (Karan)

Prepare audit-ready incident logs (Rohit)

18 Mar 26
Incident spikes

Rohit reported a spike in incidents following a recent deployment, primarily affecting authentication services.

Elena noted that similar spikes were seen in the previous deployment cycle, raising concerns about release stability.

Root cause ambiguity

Karan stated that while a configuration issue was identified, it may not fully explain all observed failures.

Rohit suggested multiple contributing factors, including increased traffic load.

Reporting gaps

Elena pointed out that some incidents discussed in the previous week’s meeting are missing from official reports.

Rohit responded that those incidents were considered “minor” and excluded.

Karan questioned the criteria for exclusion, noting lack of clear definitions.

Customer impact

Elena shared feedback from key customers experiencing intermittent failures, though not consistently reproducible.

Rohit noted that internal monitoring did not flag these issues as critical.

Metrics discussion

Karan proposed tracking “near-miss” incidents where thresholds were almost breached.

Elena agreed, noting that such signals could prevent future outages.

Ownership confusion

Rohit mentioned that some incidents were incorrectly assigned due to overlapping service ownership.

Elena suggested revisiting ownership mappings to reduce confusion.

Scope clarification

Karan highlighted that infrastructure-related incidents are sometimes mixed with application-level issues in reporting.

Rohit agreed this creates noise and suggested separate categorization.

11 Mar 2026 -
Deployment delays

Rohit confirmed that a planned deployment was postponed due to unresolved issues in staging.

Elena noted that delays have become frequent and impact delivery timelines.

Access issues

Karan reported that certain team members still lack access to critical monitoring tools.

Rohit stated that access requests are pending approval.

Data inconsistencies

Elena observed discrepancies between logs in different monitoring systems.

Rohit explained that systems are not fully synchronized, leading to mismatched data.

Coordination challenges

Karan mentioned delays in coordinating with external vendors for infrastructure fixes.

Elena added that communication gaps have contributed to slower resolution times.

Prioritization

Rohit emphasized that resolving current reliability issues takes precedence over new feature development.

Elena agreed but stressed the need to balance stability with roadmap commitments.

Request handling

Karan noted that several internal requests are being deferred due to resource constraints.

Rohit confirmed that these will be revisited after stabilizing the platform.

4. Pricing model changes and rollout

03/28/2026 -

Nisha shared an updated pricing dashboard comparing usage before and after the March 15 rollout.

Arvind asked whether the dashboard reflects discounted enterprise contracts or only standard pricing tiers.

Nisha clarified that enterprise overrides are not fully incorporated yet, which may skew revenue projections.

Sameer pointed out that this was already raised in last week’s discussion, but no update has been made since.

Nisha acknowledged the gap and said it depends on finance inputs that are still pending.

Pricing logic inconsistencies

Sameer noted that some customers are being billed under legacy pricing despite being migrated.

Arvind questioned whether this is a system issue or intentional phasing.

Nisha responded that it’s partially intentional, as some migrations were paused due to support concerns.

Sameer disagreed, saying support was not informed about any such pause.

Dashboard interpretation

Arvind mentioned that leadership interpreted the dashboard as showing a drop in revenue, which may not be accurate.

Nisha clarified that the drop is due to delayed billing cycles, not actual usage decline.

Sameer added that this nuance was not communicated in the presentation.

Billing alignment

Arvind requested that pricing reports align with invoice generation timelines instead of usage timestamps.

Nisha responded that this would require reworking the pipeline, as current reports are usage-based.

Sameer suggested maintaining both views to avoid confusion.

Internal communication gaps

Sameer highlighted that different teams are referencing different versions of the pricing model.

Arvind noted that this explains inconsistencies in customer conversations.

Nisha mentioned that documentation updates were started but not finalized.

Customer feedback

Arvind shared that some customers are confused about sudden pricing changes without clear communication.

Sameer added that support teams are receiving repeated queries about billing discrepancies.

Nisha suggested preparing a standard explanation template.

Rollback discussions

Sameer raised the possibility of rolling back certain pricing changes for affected customers.

Arvind cautioned that this could create further inconsistencies if not applied uniformly.

Nisha mentioned that partial rollbacks were already done for a few accounts, though not formally tracked.

Data pipeline issues

Nisha noted that billing data from the new system is occasionally delayed by several hours.

Sameer pointed out that this delay affects real-time dashboards shown to leadership.

Arvind suggested adding a delay indicator to avoid misinterpretation.

Follow-up tasks

Task | Assigned to | Due date | Bucket

Incorporate enterprise pricing overrides into dashboard (Nisha)

Align pricing reports with invoice timelines (Nisha, Sameer)

Prepare customer communication template for pricing changes (Sameer)

Audit migrated accounts for pricing inconsistencies (Arvind)

20 Mar 26
Migration progress

Nisha reported that most customers have been migrated to the new pricing model.

Sameer questioned this, noting that several accounts discussed earlier are still on legacy plans.

Nisha clarified that “migrated” refers to system-level changes, not billing activation.

Revenue tracking confusion

Arvind noted discrepancies between finance reports and product dashboards.

Sameer mentioned that finance is using invoice data, while product relies on usage metrics.

Nisha suggested syncing definitions but did not propose a timeline.

Customer escalations

Sameer reported an increase in escalations related to unexpected billing amounts.

Arvind asked whether these are isolated cases or part of a broader issue.

Nisha said it’s unclear due to lack of consolidated tracking.

Documentation issues

Sameer pointed out that internal documentation still reflects the old pricing structure.

Nisha acknowledged this and said updates are in progress.

Arvind noted that this was also mentioned in the previous sprint review.

Feature dependencies

Nisha explained that some pricing logic depends on features that are not fully deployed yet.

Sameer questioned why pricing was rolled out before feature completion.

Nisha responded that timelines were driven by external commitments.

Reporting gaps

Arvind highlighted that some metrics shown last week are no longer visible in the current dashboard.

Nisha said those metrics were temporarily removed due to accuracy concerns.

Sameer asked whether they will be restored.

Nisha did not confirm.

13 Mar 2026 -
Pre-rollout concerns

Sameer raised concerns about incomplete testing of the new pricing logic.

Nisha stated that core scenarios were tested, but edge cases may still exist.

Arvind suggested delaying rollout until testing is complete.

Nisha mentioned that delaying was not considered feasible at the time.

Billing edge cases

Sameer pointed out scenarios where customers switching plans mid-cycle could be billed incorrectly.

Nisha acknowledged this but said manual corrections would be applied if needed.

Arvind questioned scalability of manual fixes.

Coordination issues

Sameer noted lack of coordination between product, finance, and support teams.

Nisha agreed and said cross-team syncs were planned but not yet scheduled.

Decision ambiguity

Arvind asked who ultimately approved the pricing rollout.

Nisha said it was a joint decision, but no single owner was identified.

Sameer remarked that this makes accountability unclear.

Prioritization trade-offs

Nisha explained that pricing rollout was prioritized over stability improvements due to revenue goals.

Sameer argued that this trade-off is now causing operational issues.

Request backlog

Arvind noted that several internal requests related to pricing visibility are still pending.

Nisha confirmed they are deprioritized until rollout stabilizes.

5. 03/30/2026 – Growth experiment + onboarding issues (raw transcript)

Riya: okay so quick update on onboarding experiment—uh the new flow we pushed last week

Dev: last week as in… Thursday or earlier?

Riya: yeah Thursday… no wait rollout started Wednesday night but like partial

Kunal: only for cohort B right? not everyone

Riya: yeah not full traffic, around 40% I think

Dev: I thought it was 30… that’s what was in the doc

Riya: doc wasn’t updated, we increased it after—

Kunal: that wasn’t communicated btw

Dev: anyway conversion looks… off? like drop at step 2

Riya: yeah we saw that also but it recovers later so net is fine

Kunal: but users are dropping… recovery doesn’t matter if they don’t come back

Riya: they are coming back, just not same session

Dev: do we track that properly? I remember this came up… last sprint

Kunal: yeah we said we’d fix attribution but I don’t think it’s done

Riya: okay but overall signups increased

Dev: depends what you count as signup

Riya: completed onboarding

Kunal: that’s not signup, that’s activation

Riya: okay fine activation then

Dev: wait then what are we reporting to leadership?

Riya: same numbers as dashboard

Kunal: dashboard still shows “signups”

Dev: yeah that’s misleading

Riya: okay we can rename it

Kunal: we said that last week also

Dev: also some users are stuck in step 3, like they don’t proceed

Riya: is that the permissions screen?

Dev: yeah

Kunal: that issue was supposed to be fixed…

Riya: it was fixed for web

Dev: this is mobile

Riya: oh

Kunal: yeah mobile wasn’t included in that fix

Riya: okay that explains

Dev: but then why did we increase traffic if mobile is broken

Riya: mobile is like 20% of users

Kunal: that’s still significant

Dev: also I saw some weird spikes in drop-off yesterday

Riya: yeah that might be the tracking bug

Kunal: which one

Riya: the event firing twice

Dev: oh that’s still happening?

Riya: I thought it was fixed

Kunal: no that was only for step 1

Dev: so step 2 and 3 still double count?

Riya: maybe… not sure

Kunal: then all these numbers are… questionable

Riya: okay but directional trend is still useful

Dev: depends if the error is consistent

Kunal: it’s not

Dev: btw support flagged users complaining about “loop”

Riya: loop?

Dev: they go back to previous step after finishing

Kunal: yeah I saw that thread

Riya: is that related to the retry logic

Dev: could be

Kunal: retry logic was added… when?

Riya: mid last week

Dev: same time as rollout?

Riya: roughly

Kunal: so we changed two things at once

Dev: great

Riya: okay but loop issue is not widespread

Dev: how do we know

Riya: only like 12 tickets

Kunal: tickets != actual users

Dev: also tickets are delayed, right

Kunal: yeah usually by a day or two

Riya: okay fair

Kunal: we need better real-time signals

Dev: we said we’d add session replay

Riya: that’s still pending infra approval

Dev: okay coming back—do we pause rollout or continue?

Riya: I’d continue but fix mobile + tracking

Kunal: that’s risky

Dev: yeah feels like we’re blind

Riya: if we pause we lose momentum

Kunal: if we continue we collect bad data

Dev: already collecting bad data

Riya: okay partial rollback maybe?

Kunal: to what state

Riya: previous onboarding

Dev: but we already migrated some users

Kunal: yeah can’t fully revert

Riya: then reduce traffic?

Dev: to original 30%

Kunal: or lower

Riya: okay let’s say 25

Dev: who decides this

Kunal: good question

Riya: I can take a call for now

Dev: was this not decided earlier?

Kunal: no I think last time we said we’d review before increasing

Riya: yeah but we increased anyway

Dev: cool

Kunal: also one more thing—some users bypass onboarding entirely

Riya: how

Kunal: deep links

Dev: oh right

Riya: that was supposed to be blocked

Kunal: not fully implemented

Dev: so they skip steps but still counted?

Riya: depends

Kunal: that’s… not great

Riya: okay action items—

fix mobile permissions
fix double events
check loop issue

Dev: also attribution

Kunal: also naming (signup vs activation)

Riya: yeah

Dev: and traffic decision?

Riya: reduce to 25 for now

Kunal: temporary?

Riya: yeah until next review

Dev: when’s next review

Riya: um… Thursday?

Kunal: same as last time?

Riya: yeah

Dev: okay

(implicit references + unresolved)
“we said last sprint” → attribution fix still not done
traffic increased without formal decision
“fixed” issues actually partially fixed (web vs mobile)
metrics unreliable due to double events
conflicting definitions (signup vs activation)
rollback vs continue decision not fully resolved

6.
04/01/2026 – Infra cost spike + scaling discussion (raw transcript)

Amit: okay quick one—costs spiked yesterday… like significantly

Leena: how much is “significantly”

Amit: ~38% day-over-day

Rahul: that’s not small

Leena: is this because of the new ingestion pipeline?

Amit: partly… but not entirely

Rahul: we said this might happen when we enabled full logging

Leena: yeah but not this much

Amit: logs alone shouldn’t cause this

Rahul: unless volume increased

Leena: did it?

Amit: I mean… traffic was higher but not 38% higher

Rahul: could be retries

Leena: retries for what

Rahul: failed jobs

Amit: oh

Leena: wait are jobs failing more?

Amit: not that I saw

Rahul: we don’t really track failure rate cleanly… remember

Leena: right, that was supposed to be part of the observability thing

Amit: yeah still pending

Rahul: also yesterday we changed queue config

Leena: what change

Rahul: increased concurrency

Amit: to what

Rahul: 5x… I think

Leena: 5x??

Amit: was that tested

Rahul: kinda… on staging

Leena: staging doesn’t have real load

Amit: okay so higher concurrency → more jobs → more logs → more cost

Rahul: plus retries maybe

Leena: plus duplicate processing?

Amit: duplicate?

Leena: yeah if jobs overlap or timeout weirdly

Rahul: that did happen before

Amit: that was fixed

Rahul: partially

Leena: I thought fully

Rahul: only for one queue

Amit: how many queues do we have now

Rahul: three… or four depending how you count

Leena: great

Amit: okay so we don’t actually know which queue is causing spike

Rahul: not exactly

Leena: dashboard?

Amit: doesn’t break down by queue

Rahul: yeah we said we’d add that

Leena: when

Amit: last week

Rahul: same as… other things

Amit: okay aside from logs—compute also went up

Leena: expected with concurrency

Rahul: but not linear

Leena: meaning

Rahul: inefficiencies… idle CPU maybe

Amit: or thrashing

Leena: or autoscaling misbehaving

Rahul: oh right autoscaling

Amit: what’s current config

Rahul: aggressive scale-up

Leena: based on what metric

Rahul: queue length

Amit: if duplicates exist, queue length is inflated

Leena: so we scale more unnecessarily

Rahul: yep

Amit: okay this is getting messy

Leena: also storage costs went up

Amit: logs again?

Leena: not just logs—snapshots

Rahul: snapshots??

Leena: yeah backups every hour now

Amit: wait that was supposed to be every 6 hours

Rahul: I changed it during incident

Leena: which incident

Rahul: the one… two days ago

Amit: that wasn’t resolved yet

Leena: so we increased backup frequency permanently?

Rahul: temporary

Amit: it’s still running

Leena: okay so:

more logs
more compute
more backups

Rahul: and maybe retries

Amit: do we roll back concurrency

Leena: probably

Rahul: but throughput improved

Amit: at what cost though

Rahul: literally cost

Leena: can we reduce to 2x instead of 5x

Rahul: maybe

Amit: who set 5x anyway

Rahul: I did

Leena: based on?

Rahul: rough estimate

Amit: okay

Leena: also ingestion pipeline—are we processing all events or filtered

Amit: all events

Rahul: including debug events

Leena: why

Rahul: easier

Amit: that’s a lot of noise

Leena: yeah debug shouldn’t go to prod pipeline

Rahul: we needed it for analysis

Amit: temporary again?

Rahul: yeah

Leena: everything is temporary

Amit: okay decision time—

reduce concurrency
filter events
reduce backup frequency

Rahul: careful with backups though

Leena: yeah don’t want data loss

Amit: maybe 2 hours instead of 1

Rahul: okay

Leena: what about logs

Amit: sample them?

Rahul: or disable some

Leena: we said sampling last month

Amit: didn’t happen

Rahul: also—some services logging twice

Leena: what

Rahul: duplicate logger init

Amit: that’s… bad

Leena: so logs are doubled

Rahul: for some services yes

Amit: okay that alone could explain spike

Leena: partially

Rahul: still not full picture

Amit: do we pause ingestion?

Leena: can’t, product depends on it

Rahul: yeah that breaks features

Amit: okay so no pause

Leena: what about cost alerts

Amit: triggered late

Rahul: threshold too high

Leena: we set that also last month

Amit: yeah when costs were low

Rahul: times changed

Amit: action items—

reduce concurrency (5x → 2x)
fix duplicate logging
filter debug events
adjust backup frequency
add queue-level breakdown

Leena: and cost alerts

Rahul: and retry visibility

Amit: yeah that too

Leena: timeline?

Amit: today for quick fixes

Rahul: some of this is not “today”

Amit: okay… critical today

Leena: define critical

Rahul: exactly

Amit: fine—

concurrency
logging

rest later

Leena: okay

Rahul: sure

(implicit + contradictions + gaps)
concurrency increased without solid validation
“fixed” duplicate processing → actually partial
backups changed during incident but never reverted
debug logs unintentionally flowing into prod pipeline
duplicate logging inflating costs
no clear ownership for infra decisions
cost alerts configured for old baseline
multiple “temporary” changes became permanent04/01/2026 – Infra cost spike + scaling discussion (raw transcript)

Amit: okay quick one—costs spiked yesterday… like significantly

Leena: how much is “significantly”

Amit: ~38% day-over-day

Rahul: that’s not small

Leena: is this because of the new ingestion pipeline?

Amit: partly… but not entirely

Rahul: we said this might happen when we enabled full logging

Leena: yeah but not this much

Amit: logs alone shouldn’t cause this

Rahul: unless volume increased

Leena: did it?

Amit: I mean… traffic was higher but not 38% higher

Rahul: could be retries

Leena: retries for what

Rahul: failed jobs

Amit: oh

Leena: wait are jobs failing more?

Amit: not that I saw

Rahul: we don’t really track failure rate cleanly… remember

Leena: right, that was supposed to be part of the observability thing

Amit: yeah still pending

Rahul: also yesterday we changed queue config

Leena: what change

Rahul: increased concurrency

Amit: to what

Rahul: 5x… I think

Leena: 5x??

Amit: was that tested

Rahul: kinda… on staging

Leena: staging doesn’t have real load

Amit: okay so higher concurrency → more jobs → more logs → more cost

Rahul: plus retries maybe

Leena: plus duplicate processing?

Amit: duplicate?

Leena: yeah if jobs overlap or timeout weirdly

Rahul: that did happen before

Amit: that was fixed

Rahul: partially

Leena: I thought fully

Rahul: only for one queue

Amit: how many queues do we have now

Rahul: three… or four depending how you count

Leena: great

Amit: okay so we don’t actually know which queue is causing spike

Rahul: not exactly

Leena: dashboard?

Amit: doesn’t break down by queue

Rahul: yeah we said we’d add that

Leena: when

Amit: last week

Rahul: same as… other things

Amit: okay aside from logs—compute also went up

Leena: expected with concurrency

Rahul: but not linear

Leena: meaning

Rahul: inefficiencies… idle CPU maybe

Amit: or thrashing

Leena: or autoscaling misbehaving

Rahul: oh right autoscaling

Amit: what’s current config

Rahul: aggressive scale-up

Leena: based on what metric

Rahul: queue length

Amit: if duplicates exist, queue length is inflated

Leena: so we scale more unnecessarily

Rahul: yep

Amit: okay this is getting messy

Leena: also storage costs went up

Amit: logs again?

Leena: not just logs—snapshots

Rahul: snapshots??

Leena: yeah backups every hour now

Amit: wait that was supposed to be every 6 hours

Rahul: I changed it during incident

Leena: which incident

Rahul: the one… two days ago

Amit: that wasn’t resolved yet

Leena: so we increased backup frequency permanently?

Rahul: temporary

Amit: it’s still running

Leena: okay so:

more logs
more compute
more backups

Rahul: and maybe retries

Amit: do we roll back concurrency

Leena: probably

Rahul: but throughput improved

Amit: at what cost though

Rahul: literally cost

Leena: can we reduce to 2x instead of 5x

Rahul: maybe

Amit: who set 5x anyway

Rahul: I did

Leena: based on?

Rahul: rough estimate

Amit: okay

Leena: also ingestion pipeline—are we processing all events or filtered

Amit: all events

Rahul: including debug events

Leena: why

Rahul: easier

Amit: that’s a lot of noise

Leena: yeah debug shouldn’t go to prod pipeline

Rahul: we needed it for analysis

Amit: temporary again?

Rahul: yeah

Leena: everything is temporary

Amit: okay decision time—

reduce concurrency
filter events
reduce backup frequency

Rahul: careful with backups though

Leena: yeah don’t want data loss

Amit: maybe 2 hours instead of 1

Rahul: okay

Leena: what about logs

Amit: sample them?

Rahul: or disable some

Leena: we said sampling last month

Amit: didn’t happen

Rahul: also—some services logging twice

Leena: what

Rahul: duplicate logger init

Amit: that’s… bad

Leena: so logs are doubled

Rahul: for some services yes

Amit: okay that alone could explain spike

Leena: partially

Rahul: still not full picture

Amit: do we pause ingestion?

Leena: can’t, product depends on it

Rahul: yeah that breaks features

Amit: okay so no pause

Leena: what about cost alerts

Amit: triggered late

Rahul: threshold too high

Leena: we set that also last month

Amit: yeah when costs were low

Rahul: times changed

Amit: action items—

reduce concurrency (5x → 2x)
fix duplicate logging
filter debug events
adjust backup frequency
add queue-level breakdown

Leena: and cost alerts

Rahul: and retry visibility

Amit: yeah that too

Leena: timeline?

Amit: today for quick fixes

Rahul: some of this is not “today”

Amit: okay… critical today

Leena: define critical

Rahul: exactly

Amit: fine—

concurrency
logging

rest later

Leena: okay

Rahul: sure

(implicit + contradictions + gaps)
concurrency increased without solid validation
“fixed” duplicate processing → actually partial
backups changed during incident but never reverted
debug logs unintentionally flowing into prod pipeline
duplicate logging inflating costs
no clear ownership for infra decisions
cost alerts configured for old baseline
multiple “temporary” changes became permanent

7.
04/02/2026 – Sales pipeline + forecasting issues (raw transcript)

Megha: okay quick sync on pipeline—numbers from yesterday look… inflated

Siddharth: inflated how

Megha: total pipeline jumped like 25% overnight

Arjun: that sounds good?

Megha: not really… I don’t think it’s real

Siddharth: is this because of the bulk import

Megha: yeah partly

Arjun: those were old leads though

Megha: exactly

Siddharth: wait so we added old leads into active pipeline?

Megha: they got tagged as “open”

Arjun: that’s wrong

Megha: yeah but system default did that

Siddharth: didn’t we fix this last time

Megha: for manual entries, not imports

Arjun: okay so pipeline includes stale leads

Megha: yes

Siddharth: how many

Megha: not sure… maybe 30–40%

Arjun: that’s huge

Siddharth: okay then forecast is also off

Megha: yeah forecast is based on pipeline

Arjun: so leadership saw wrong numbers

Megha: already shared in morning update

Siddharth: great

Arjun: can we retract

Megha: not sure… maybe clarify later

Siddharth: also stages are messy

Megha: yeah I noticed deals jumping stages

Arjun: jumping how

Megha: like from “contacted” to “negotiation” directly

Siddharth: that shouldn’t happen

Arjun: unless manually updated

Megha: or automation

Siddharth: which automation

Megha: the scoring-based one

Arjun: oh that thing… we said to disable it

Megha: I thought it was disabled

Siddharth: maybe partially

Arjun: partially disabled??

Megha: some rules still active I think

Siddharth: so deals auto-move based on score

Arjun: that breaks forecasting

Megha: yeah because stage probability changes

Siddharth: exactly

Arjun: okay what about conversion rates

Megha: also weird

Siddharth: define weird

Megha: higher than usual

Arjun: that’s because deals skip stages

Siddharth: so funnel is compressed

Megha: yeah

Arjun: okay so:

inflated pipeline
incorrect stages
wrong conversion

Megha: pretty much

Siddharth: what about duplicates

Megha: oh yeah… that too

Arjun: what

Megha: some leads got duplicated during import

Siddharth: how many

Megha: not sure… depends on email matching

Arjun: I thought deduplication was in place

Megha: only exact match

Siddharth: so variations slip through

Arjun: great

Megha: also some deals have no owner

Siddharth: why

Megha: import again

Arjun: so they’re just sitting there

Megha: yeah

Siddharth: are those counted in pipeline

Megha: yes

Arjun: that’s misleading

Megha: okay also—some closed deals reopened

Siddharth: what

Arjun: why

Megha: sync issue with billing

Siddharth: again??

Arjun: we fixed that last month

Megha: apparently not fully

Siddharth: so revenue numbers also affected

Megha: possibly

Arjun: okay this is bad

Siddharth: what’s the plan

Megha: cleanup first

Arjun: define cleanup

Megha:

remove stale leads
fix duplicates
assign owners

Siddharth: and stages

Arjun: and automation

Megha: yeah disable automation fully

Siddharth: confirm it this time

Arjun: what about forecast already shared

Megha: send correction

Siddharth: with explanation

Arjun: careful how we word it

Megha: also long-term we need better pipeline hygiene

Siddharth: yeah we say this every time

Arjun: because it keeps happening

Megha: maybe validation rules

Siddharth: like what

Megha:

no deal without owner
no stage skipping

Arjun: can we enforce that

Megha: technically yes

Siddharth: what about imports

Megha: that’s tricky

Arjun: imports always break things

Megha: also scoring model… do we keep it

Siddharth: not until stable

Arjun: agree

Megha: okay disable for now

Siddharth: timeline

Megha: cleanup today… ideally

Arjun: “ideally”

Megha: okay critical fixes today

Siddharth: which are

Megha:

remove stale leads
disable automation

Arjun: duplicates?

Megha: might take longer

Siddharth: owners?

Megha: also later

Arjun: so pipeline still wrong

Megha: less wrong

Siddharth: okay

(implicit + contradictions + failure modes)
“pipeline growth” actually due to stale imported leads
automation partially disabled → causing stage jumps
duplicates slipping through due to weak matching
closed deals reopening due to billing sync issue (not fully fixed)
forecast shared externally before validation
unclear ownership for cleanup tasks
repeated pattern: “we said this last time” but no systemic fix
partial fixes prioritized → system remains inconsistent

8.
