# FIST Client Libraries

This directory contains client libraries for easy integration with the FIST Content Moderation API in different programming languages.

## Available Client Libraries

### Python Client (`python/fist_client.py`)

A comprehensive Python client library for the FIST API.

#### Installation

```bash
# Copy the fist_client.py file to your project
cp client_libraries/python/fist_client.py your_project/

# Install required dependencies
pip install requests
```

#### Quick Start

```python
from fist_client import FistClient

# Initialize client
client = FistClient(
    token="fist_your_token_here",
    base_url="https://your-fist-api.com"
)

# Single content moderation
result = client.moderate_content("Some text to moderate")
print(f"Decision: {result.final_decision} ({result.inappropriate_probability}%)")

# Batch processing
contents = ["Text 1", "Text 2", "Text 3"]
results = client.moderate_batch(contents)
print(f"Processed {len(results)} items")

# Background batch processing
batch_job = client.moderate_batch(contents, background=True)
print(f"Job ID: {batch_job.job_id}, Status: {batch_job.status}")

# Check system health
health = client.get_health()
print(f"System status: {health['status']}")
```

#### Features

- **Simple API**: Easy-to-use methods for all FIST endpoints
- **Automatic Retries**: Built-in retry logic with exponential backoff
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Batch Processing**: Support for both sync and async batch processing
- **Monitoring**: Access to system health and performance metrics
- **Type Safety**: Full type hints and structured response objects

### JavaScript Client (`javascript/fist-client.js`)

A versatile JavaScript client library that works in both Node.js and browser environments.

#### Installation

**Node.js:**
```bash
# Copy the fist-client.js file to your project
cp client_libraries/javascript/fist-client.js your_project/

# Install node-fetch for Node.js environments
npm install node-fetch
```

**Browser:**
```html
<!-- Include the client library -->
<script src="fist-client.js"></script>
```

#### Quick Start

**Node.js (CommonJS):**
```javascript
const { FistClient } = require('./fist-client');

const client = new FistClient({
    token: 'fist_your_token_here',
    baseUrl: 'https://your-fist-api.com'
});

// Single content moderation
const result = await client.moderateContent('Some text to moderate');
console.log(`Decision: ${result.finalDecision} (${result.inappropriateProbability}%)`);

// Batch processing
const contents = ['Text 1', 'Text 2', 'Text 3'];
const results = await client.moderateBatch(contents);
console.log(`Processed ${results.length} items`);
```

**ES6 Modules:**
```javascript
import { FistClient } from './fist-client.js';

const client = new FistClient({
    token: 'fist_your_token_here',
    baseUrl: 'https://your-fist-api.com'
});

// Use same API as above
```

**Browser (Global):**
```javascript
const client = new FistClient({
    token: 'fist_your_token_here',
    baseUrl: 'https://your-fist-api.com'
});

// Use same API as above
```

#### Features

- **Universal**: Works in Node.js and browser environments
- **Modern JavaScript**: Uses async/await and modern JavaScript features
- **Automatic Retries**: Built-in retry logic with exponential backoff
- **Error Handling**: Comprehensive error handling with custom error classes
- **Batch Processing**: Support for both sync and async batch processing
- **Monitoring**: Access to system health and performance metrics
- **Multiple Module Systems**: Supports CommonJS, ES6 modules, and global variables

## Common Usage Patterns

### Error Handling

**Python:**
```python
from fist_client import FistClient, AuthenticationError, APIError

try:
    client = FistClient(token="invalid_token")
    result = client.moderate_content("test")
except AuthenticationError:
    print("Invalid token")
except APIError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
```

**JavaScript:**
```javascript
import { FistClient, AuthenticationError, APIError } from './fist-client.js';

try {
    const client = new FistClient({ token: 'invalid_token' });
    const result = await client.moderateContent('test');
} catch (error) {
    if (error instanceof AuthenticationError) {
        console.log('Invalid token');
    } else if (error instanceof APIError) {
        console.log(`API error: ${error.message} (status: ${error.statusCode})`);
    }
}
```

### Batch Processing with Progress Tracking

**Python:**
```python
# Start background batch job
batch_job = client.moderate_batch(large_content_list, background=True)

# Poll for progress
while True:
    status = client.get_batch_status(batch_job.job_id)
    print(f"Progress: {status.progress_percent}%")
    
    if status.status == "completed":
        results = client.get_batch_results(batch_job.job_id)
        break
    elif status.status == "failed":
        print("Batch job failed")
        break
    
    time.sleep(2)
```

**JavaScript:**
```javascript
// Start background batch job
const batchJob = await client.moderateBatch(largeContentList, { background: true });

// Poll for progress
while (true) {
    const status = await client.getBatchStatus(batchJob.jobId);
    console.log(`Progress: ${status.progressPercent}%`);
    
    if (status.status === 'completed') {
        const results = await client.getBatchResults(batchJob.jobId);
        break;
    } else if (status.status === 'failed') {
        console.log('Batch job failed');
        break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
}
```

### Custom Configuration

**Python:**
```python
client = FistClient(
    token="fist_your_token",
    base_url="https://your-api.com",
    timeout=60,
    max_retries=5,
    retry_delay=2.0
)

# Custom moderation parameters
result = client.moderate_content(
    "content to moderate",
    percentages=[0.9, 0.7, 0.5, 0.3],
    thresholds=[300, 800, 2000],
    probability_thresholds={"low": 15, "high": 85}
)
```

**JavaScript:**
```javascript
const client = new FistClient({
    token: 'fist_your_token',
    baseUrl: 'https://your-api.com',
    timeout: 60000,
    maxRetries: 5,
    retryDelay: 2000
});

// Custom moderation parameters
const result = await client.moderateContent('content to moderate', {
    percentages: [0.9, 0.7, 0.5, 0.3],
    thresholds: [300, 800, 2000],
    probabilityThresholds: { low: 15, high: 85 }
});
```

## API Reference

### Core Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `moderateContent(content, options)` | Moderate single content | `ModerationResult` |
| `moderateBatch(contents, options)` | Moderate multiple contents | `ModerationResult[]` or `BatchJob` |
| `getBatchStatus(jobId)` | Get batch job status | `BatchJob` |
| `getBatchResults(jobId)` | Get batch job results | `ModerationResult[]` |
| `getHealth()` | Get system health | `Object` |
| `getMetrics()` | Get performance metrics | `Object` |
| `getCacheStats()` | Get cache statistics | `Object` |
| `clearCache()` | Clear system cache | `Object` |
| `testConnection()` | Test API connection | `boolean` |

### Response Objects

#### ModerationResult
- `moderationId`: Unique moderation ID
- `contentHash`: SHA-256 hash of content
- `inappropriateProbability`: AI probability score (0-100)
- `aiReason`: AI assessment reason
- `finalDecision`: Final decision (A/R/M)
- `reason`: Decision explanation
- `wordCount`: Original content word count
- `percentageUsed`: Percentage of content analyzed
- `createdAt`: Timestamp
- `fromCache`: Whether result came from cache

#### BatchJob
- `jobId`: Unique job ID
- `status`: Job status (pending/processing/completed/failed)
- `totalItems`: Total items in batch
- `processedItems`: Items processed so far
- `progressPercent`: Progress percentage
- `createdAt`: Job creation timestamp
- `startedAt`: Processing start timestamp
- `completedAt`: Completion timestamp

## Contributing

To add support for additional programming languages:

1. Create a new directory under `client_libraries/`
2. Implement the core client functionality
3. Follow the same API patterns as existing clients
4. Add comprehensive error handling
5. Include usage examples and documentation
6. Update this README with the new client information

## Support

For issues with the client libraries:

1. Check the main FIST API documentation
2. Verify your API token and permissions
3. Test the connection using the `testConnection()` method
4. Check the system health using `getHealth()`
5. Review error messages and status codes

For API-specific issues, refer to the main FIST documentation and API endpoints.
