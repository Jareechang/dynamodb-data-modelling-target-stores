# Dynamodb Data modelling: Target stores (WIP)

Data modelling demo with DynamoDB using terraform for infrastructure management.

This demostration goes from the raw data to designing and planning a DyanmoDB store for the given access patterns provided.

## Table Of Contents:

- [Introduction](#Introdiction)
- [Quick Start](#quick-start)
- [Analyze Data](#design---analyze-data)
- [DynamoDB Indexes](#design---dynamodb-indexes)
- [Data Transformation](#design---data-transformation)
- [Optimization](#) TODO

## Introduction

Design an efficient dynamodb with the data and the provided access patterns.

Please note this is work in process.

**Access Patterns:**

- Given ID, return all attributes for store (ID: 1957).
- Return all stores that do not observe daylight savings time; return just state and store ID.
- Given a phone area code, return all stores with formatted addresses and phone numbers (Area Code: 206).
- Return all attributes for all stores with Starbucks and CVS.
- Given state, return all attributes for all stores (State: WA).
- Given state and city, return all attributes for all stores (State: WA; City: Seattle).
- Given state city and zip, return all attributes for all stores (State: WA; City: Seattle; Zip: 98125).

**Core Concepts:**

- Leverage AWS DynamoDB GSI / LSI
- Leverage AWS Querying 
- DynamoDB Design with GSI Sparse indexes
- DynamoDB Design with GSI Composite keys  

## Quick Start

**Technologies:**

- AWS DynamoDB
- Terraform (>= v0.12.24)
- Python / Typescript

1. Start local DynamoDB & Create Table(for local testing)  

```sh
# Start local dynamodb
docker compose up

# Create table using terraform (Use Option 1 or 2)

# Option 1, Env: local (Mock dynamoDB)
terraform plan -auto-approve -var-file=./env/local.tfvars
terraform apply -auto-approve -var-file=./env/local.tfvars

# Option 2, Env: Dev (Use a real service from AWS)
terraform plan -var-file=./env/dev.tfvars
terraform apply -auto-approve -var-file=./env/dev.tfvars

# IMPORTANT: Remember to destroy resources after finishing with testing it otherwise you will incur charges
terraform destroy -auto-approve -var-file=./env/dev.tfvars
```

**Note:** `-var-file=./env/local.tfvars` points the dynamodb to the local endpoint if you want to use local dyamodb (local dev)

2. Create the insert json (Using python)  

```sh
python ./scripts/generate.py
```

3. Insert Into Table (Using Node.js)   

```sh
# Install packages
yarn

# Insert data into db 
yarn run build && yarn run insert-db
```
## Design - Analyze Data

1. Identify 'Entities' based on the access patterns  

**Query Entities:**
- Store

2. Identify 'Attributes' based on the access patterns

**Query Attributes:**

- ID (number) 
- IsDaylightSavingsTimeRecognized (string) 
- Address.FormattedAddress (string)
- PhoneNumber (string) 
- Address.Subdivision, "state" (string) 
- Address.City (string) 
- AllCapability (string[])
- PostalCode (string) 

3. Identify 'Attribute' restrictions

- ID must be unique (Store ID)

## Design - DynamoDB Indexes

1. Given state, return all attributes for all stores (State: WA).  

**This be the PK/SK of the base table**

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| BASE | Address.Subdivision | ID | None (Base Table) |

**AWS CLI query:**
```sh
# Change the --endpoint-url if using a different environment
# Note: Remove the --select "Count" if you like to see all projections from DB

aws dynamodb query \
--endpoint-url "http://localhost:8000/" \
--table-name Store \
--select "COUNT" \
--index-name "Query-By-Store-State" \
--key-condition-express "#state = :v"  \
--expression-attribute-names "{\"#state\":\"Address.Subdivision\"}" \
--expression-attribute-values "{\":v\": {\"S\": \"WA\"}}"
```

2. Given ID, return all attributes for store (ID: 1957)

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| GSI | ID | Address.Subdivision | ALL |

**Implementation:** `ID = '<Store-ID>'`

3. Return all stores that do not observe daylight savings time; return just state and store ID.

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| GSI | IsDaylightSavingsTimeRecognized | None | KEYS (Base PK/SK) |

**Implementation:** `IsDaylightSavingsTimeRecognized = 'TRUE' | 'FALSE'`

4. Given a phone area code, return all stores with formatted addresses and phone numbers (Area Code: 206).

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| LSI | X.locale | PhoneNumber | All |

**Implementation:** `X.locale = '<locale>' and begins_with('(<area-code>)')`


5. Return all attributes for all stores with Starbucks and CVS.

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| LSI | Starbucks | CVS | KEYS (Base PK/SK) |

- Add new Fields `Starbucks` ("EXISTS" or blank)
- Add new Fields `CVS` ("EXISTS" or blank)

**Note:** *For any item in a table, DynamoDB writes a corresponding index entry only if the index sort key value is present in the item.* We will leverage the sparse indexing.

**AWS CLI query:**

```sh
# Change the --endpoint-url if using a different environment
# Note: Remove the --select "Count" if you like to see all projections from DB

aws dynamodb query \
--endpoint-url "http://localhost:8000/" \
--select "COUNT" \
--table-name Store \
--projection-expression "ID" \
--index-name "Query-By-Starbucks-And-CSV" \
--key-condition-express "#sb = :v and #cvs = :v"  \
--expression-attribute-names "{\"#sb\":\"Starbucks\", \"#cvs\":\"CVS\"}" \
--expression-attribute-values "{\":v\": {\"S\": \"True\"}}"
```

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| GSI | IsDaylightSavingsTimeRecognized | None | KEYS (Base PK/SK) |

**Implementation:** `IsDaylightSavingsTimeRecognized = 'FALSE'`

6. Given state and city, return all attributes for all stores (State: WA; City: Seattle).

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| LSI | Address.Subdivision | CityZip | KEYS (Base PK/SK) |

**Pre-computed key (composite key):** `Address.Subdivision` and `Address.PostalCode` named `CityZip` separated by #

**Implementation:** `state = '<State>' and CityZip begins_with('<city>')`

7. Given state city and zip, return all attributes for all stores (State: WA; City: Seattle; Zip: 98125).

Same as #7.

**Pre-computed key (composite key):** `Address.Subdivision` and `Address.PostalCode` named `CityZip` separated by #

**Implementation:** `state = '<State>' and CityZip begins_with('<city>#<zip>')`

## Design - Data Transformation 

Below are the final list of data we need to extract from the raw data to insert into dyanmoDB to support the query patterns above. 

**Query Attributes:**

- ID (number) 
- IsDaylightSavingsTimeRecognized (string) 
- Address.FormattedAddress (string)
- PhoneNumber, FaxNumber (string) 
- Address.Subdivision, "state" (string) 
- Address.City (string) 
- AllCapability (string[])
- Address.PostalCode (string) 
- X.locale (string)

**Custom Attributes:**

- `CitZip` - Address.Subdivision#Address.PostalCode(string)
- `Starbucks` (string)
- `CVS` (string)

**GSI:**

1. Query-By-Store-State - PK: Address.Subdivision, SK: ID
2. Query-By-DayLightSavings - PK: IsDaylightSavingsTimeRecognized, SK: None
3. Query-By-Phone-Area-Code - PK: X.Locale, SK: PhoneNumber
4. Query-By-Starbucks-And-CSV - PK: Starbucks, SK: CVS (Sparse indexing)

**LSI:**

5. Query-By-State-CityZip - PK: ADdress.Subdivision (by default), SK: CityZip
