Go to Settings Inventory -> Shipping Scheduler

to apply globally set:
* Use global Assignation Limit
* set horizon
- start timezone to count horizon will be UTC, so if you set 2 day it will be UTC time + 2 days

to apply for company:
* Scheduler Assignation Limit
* set horizon
* go to Sceduled actions find "Procurement: run scheduler" add company to args

model.run_scheduler(True, company_id=1)

where 1 is id of company for which scheduler should run
- start timezone in this case will company timezone

to have scheduler for another company copy method just change the id of company or copy all cron and set another company there
