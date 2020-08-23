import fs from 'fs';
import AWS from 'aws-sdk';

class DynamoDBWrapper {
    private ddb: any;

    constructor() {
        this.ddb = new AWS.DynamoDB({
            endpoint: process.env.AWS_DDB_ENDPOINT || 'http://localhost:8000',
            region: process.env.AWS_DDB_REGION || 'us-east-1',
            apiVersion: '2012-08-10'
        }); 
    }

    public async batchWrite(
        items: any 
    ): Promise<any> {
        const putRequests = items.map((item: any) : any => {
            return this.generatePutRequest(AWS.DynamoDB.Converter.marshall(item));
        });
        const batchWriteParams = {
            RequestItems: {
                "Store": [
                    ...putRequests
                ]
            }
        };

        return this.ddb.batchWriteItem(batchWriteParams).promise();
    }

    private generatePutRequest(item: unknown) : any {
        return {
            PutRequest: {
                Item: item
            }
        }
    }
}

async function main() {
    const rawData = await fs.promises.readFile('./ddb-inserts.json', 'utf8');
    const results = JSON.parse(rawData);
    const ddbWrapper = new DynamoDBWrapper();
    let batchWriteEntries : Array<any> = [];
    let entriesInserted : number = 0;
    const operations : Array<Promise<any>> = [];
    results.forEach(async(data: any, i: number) : Promise<void> => {
        batchWriteEntries.push(data);
        // Insert every 10 items batch write limit = 25 ops or < 16 mb
        if (i % 10 === 0) {
            operations.push(ddbWrapper.batchWrite(batchWriteEntries).catch(err => console.log(err)));
            entriesInserted += batchWriteEntries.length
            // Reset the entries
            batchWriteEntries = [];
        }
    });

    await Promise.all(operations)
        .then((_) => {
            console.log(`${entriesInserted} inserted into DynamoDB.`);
        })
}

main();
