
# Local Vars 
locals {
    ddb_endpoint = var.env == "local" ? var.local_ddb_endpoint : "http://dynamodb.${var.aws_region}.amazonaws.com"
    ddb_default_write_cap = 5
    ddb_default_read_cap = 5
}

provider "aws" {
  version = "~> 2.0"
  region  = var.aws_region

  # Skip the AWS validation steps
  skip_credentials_validation = var.env == "local" ? true : false
  skip_requesting_account_id  = var.env == "local" ? true : false

  endpoints {
      dynamodb = local.ddb_endpoint # Point to endpoint depending on env
  }
}

resource "aws_dynamodb_table" "target_store" {
    name           = "Store"
    billing_mode   = "PROVISIONED"
    read_capacity  = 5
    write_capacity = 5
    hash_key       = "Address.Subdivision"
    range_key      = "ID"

    attribute {
        name = "Address.Subdivision"
        type = "S"
    }

    attribute {
        name = "ID"
        type = "N"
    }

    attribute {
        name = "IsDaylightSavingsTimeRecognized"
        type = "S"
    }

    attribute {
        name = "X.Locale"
        type = "S"
    }

    attribute {
        name = "PhoneNumber"
        type = "S"
    }

    # Custom - Fields that are not in original data set but are pre-computed for dynamodb
    
    attribute {
        name = "CityZip"
        type = "S"
    }

    attribute {
        name = "Starbucks"
        type = "S"
    }

    attribute {
        name = "CVS"
        type = "S"
    }

    ttl {
        attribute_name = "TimeToExist"
        enabled        = false
    }

    # Query by store ID - Given ID, return all attributes for store (ID: 1957)
    global_secondary_index {
        name               = "Query-By-Store-ID"
        hash_key           = "ID"
        range_key          = "Address.Subdivision"
        write_capacity     = local.ddb_default_write_cap
        read_capacity      = local.ddb_default_read_cap
        projection_type    = "ALL"
    }

    # Query by store that do not observe day light saving 
    global_secondary_index {
        name               = "Query-By-DayLightSavings"
        hash_key           = "IsDaylightSavingsTimeRecognized"
        #range_key         = ""  # Omitted range key
        write_capacity     = local.ddb_default_write_cap
        read_capacity      = local.ddb_default_read_cap
        projection_type    = "KEYS_ONLY"
    }

    # Given a phone area code, return all stores with formatted addresses and phone numbers (Area Code: 206).
    global_secondary_index {
        name               = "Query-By-Phone-Area-Code"
        hash_key           = "X.Locale"
        range_key          = "PhoneNumber" # Omitted range key
        write_capacity     = local.ddb_default_write_cap
        read_capacity      = local.ddb_default_read_cap
        projection_type    = "ALL"
    }

    # Return all attributes for all stores with Starbucks and CVS.
    global_secondary_index {
        name               = "Query-By-Starbucks-And-CSV"
        hash_key           = "Starbucks"
        range_key          = "CVS"
        write_capacity     = local.ddb_default_write_cap
        read_capacity      = local.ddb_default_read_cap
        projection_type    = "ALL"
    }

    # Query by State, City and Zip
    # Query 1 : Given state and city, return all attributes for all stores (State: WA; City: Seattle).
    # Query 2 : Given state city and zip, return all attributes for all stores (State: WA; City: Seattle; Zip: 98125).
    local_secondary_index {
        name               = "Query-By-State-CityZip"
        range_key          = "CityZip"
        projection_type    = "ALL"
    }

    tags = {
        Name        = "dynamodb-table-store-${var.env}" # convention: dyanmodb-table-store-{env}
        Environment = var.env
    }
}
