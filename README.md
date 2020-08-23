# Dynamodb Data modelling: Target stores (WIP)

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

#### Contents:

- [Quick Start](#quick-start)
- [Analyze Data](#design-analyze-data)
- [DynamoDB Indexes](#design-dynamodb-indexes)
- [Data Transformation](#design-data-transformation)

## Quick Start

1. Start local DynamoDB & Create Table(for local testing)  

```
# Start local dynamodb
docker compose up

# Create local dynamodb
aws dynamodb create-table \
    --endpoint-url "http://localhost:8000/" \
    --table-name Store \
    --attribute-definitions AttributeName=N,AttributeType=S AttributeName=Address.Subdivision,AttributeType=S \
    --key-schema AttributeName=Address.Subdivision,KeyType=HASH AttributeName=ID,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1
```

2. Create the insert json (Using python)  

```python
python ./scripts/generate.py
```

3. Insert Into Table (Using Node.js)   

```python
yarn run dev
```
## Design - Analyze Data

1. Identify 'Entities' based on the access patterns  

**Query Entities:**
- Store

2. Identify 'Attributes' based on the access patterns

**Query Attributes:**

- ID (string) 
- IsDaylightSavingsTimeRecognized (string) 
- Address.FormattedAddress (string)
- PhoneNumber, FaxNumber (string) 
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
| BASE | State | ID | None (Base Table) |

**implementation:** `state = '<State>'`

2. Given ID, return all attributes for store (ID: 1957)

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| GSI | ID | Address.Subdivision | ALL |

**implementation:** `ID = '<Store-ID>'`

3. Return all stores that do not observe daylight savings time; return just state and store ID.

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| GSI | IsDaylightSavingsTimeRecognized | None | KEYS (Base PK/SK) |

**implementation:** `IsDaylightSavingsTimeRecognized = 'TRUE' | 'FALSE'`

4. Given a phone area code, return all stores with formatted addresses and phone numbers (Area Code: 206).

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| LSI | X.Locale | PhoneNumber | All |

**implementation:** `X.Locale = '<locale>' and begins_with('(<area-code>)')`

5. Return all stores that do not observe daylight savings time; return just state and store ID.

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| GSI | IsDaylightSavingsTimeRecognized | None | KEYS (Base PK/SK) |

**implementation:** `IsDaylightSavingsTimeRecognized = 'TRUE' | 'FALSE'`

6. Return all attributes for all stores with Starbucks and CVS.

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| GSI | IsDaylightSavingsTimeRecognized | None | KEYS (Base PK/SK) |

7. Given state and city, return all attributes for all stores (State: WA; City: Seattle).

Index Type | PK | SK| Projections |
------------ | -------------| -------------| -------------
| LSI | Address.Subdivision | CityZip | KEYS (Base PK/SK) |

**Pre-computed key:** `Address.Subdivision` and `Address.PostalCode` named `CityZip` separated by #

**implementation:** `state = '<State>' and CityZip begins_with('<city>')`

8. Given state city and zip, return all attributes for all stores (State: WA; City: Seattle; Zip: 98125).

Same as #7.

**implementation:** `state = '<State>' and CityZip begins_with('<city>#<zip>')`

## Design - Data Transformation 

Below are the final list of data we need to extract from the raw data to insert into dyanmoDB to support the query patterns above. 

**Query Attributes:**

- ID (string) 
- IsDaylightSavingsTimeRecognized (string) 
- Address.FormattedAddress (string)
- PhoneNumber, FaxNumber (string) 
- Address.Subdivision, "state" (string) 
- Address.City (string) 
- AllCapability (string[])
- Address.PostalCode (string) 
- X.Locale
- `Address.Subdivision#Address.PostalCode`

**GSI/LSI:**

- CityZip 'CITY#ZIP'
