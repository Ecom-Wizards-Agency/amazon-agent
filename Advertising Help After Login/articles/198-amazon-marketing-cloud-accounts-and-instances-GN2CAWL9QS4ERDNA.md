---
title: "Amazon Marketing Cloud accounts and instances"
source_url: "https://advertising.amazon.com/help/GN2CAWL9QS4ERDNA"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Amazon Marketing Cloud accounts and instances

Learn how Amazon Marketing Cloud (AMC) is organized via accounts and instance objects.

Updated on Feb 25, 2026

AMC has 2 primary organizational objects: accounts and instances. An AMC account can contain one or more instances, and typically maps to a corporation or agency. An AMC instance contains Amazon Ads events for a single advertiser and can be mapped to multiple Amazon DSP accounts and sponsored ads entities.

An AMC user can be permitted to one or more AMC accounts and one or more instances within each account. This structure enables AMC administrators to provide AMC account access without providing access to all the AMC instances within the AMC account.

## AMC account

As described above, an AMC account is an organizational object that can contain one or more AMC instances, and typically maps to a corporation or agency. When an AMC account is created, the owner of the account elects an administrator from within their organization. This administrator is responsible for AMC access management, among other things. Learn more about administrator tasks by visiting User management.

The identifier of your AMC account may be helpful for use in troubleshooting, instance requests, or other purposes. To determine your AMC account ID, access the AMC console with your credentials. The URL will contain an alphanumeric code that is prefixed with “ENTITY“; this is your AMC account identifier. An example of an AMC account identifier (entity identifier) is: ENTITY1AA1AA11AAA1.

## AMC instance

AMC is an instanced product. An AMC instance is the actual “clean room” in which you’ll generate analytics and build audiences. Each instance contains records from only a single advertiser. Some advertisers may have multiple Amazon DSP and sponsored ads entities that represent different business units, brands, or subsidiaries. As long as those entities all represent the same company advertising on Amazon, they can be linked to the same AMC instance. Alternatively, the advertiser may choose to create 1 instance for each of their brands (see screenshot below). Note that while you can perform queries within each instance, you can’t perform queries across instances.

Instance creation is managed by Amazon; you must work with your Amazon representative to make an instance request. Once created, you’ll be able to start querying the records in your AMC instances. Each instance will contain at most 12.5 months of your Amazon Ads events. To understand how far back the records in your AMC instance go, refer to the below guidance:

- For instances live for under 12.5 months: If created after August 2023, they’ll contain records from July 1, 2023 onward. If created on July 2023 or earlier, the earliest record dates will vary based on date of creation. Query your AMC instance directly to determine the start date of your records.
- For instances that have been live for over 12.5 months, they’ll contain the most recent 12.5 months of records, with older records having aged out.
