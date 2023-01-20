Release type: patch

This release fixes a bug in subscriptions using the graphql-transport-ws protocol
where the conversion of the NextMessage object to a dictionary took an unnecessary 
amount of time leading to an increase in CPU usage.