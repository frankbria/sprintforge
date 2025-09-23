# Excel-Server Two-Way Sync Architecture

## Overview

This document outlines the technical architecture for enterprise-friendly two-way synchronization between Excel spreadsheets and the SprintForge server. The design prioritizes security, data integrity, and compatibility with enterprise IT policies while maintaining a seamless user experience.

## Core Architecture

### The Challenge

Excel files aren't databases - they're binary blobs with complex internal structures. The sync system must:

1. Parse uploaded Excel files to extract changes
2. Detect what changed vs. last known state
3. Merge changes without conflicts
4. Regenerate Excel with updates from other users
5. Maintain complete audit trail

### Technology Stack

```python
# Server-Side Stack
- FastAPI (REST endpoints)
- OpenPyXL (Excel parsing/generation)
- PostgreSQL (source of truth)
- Redis (session/cache layer)
- MinIO/S3 (file storage)
- Temporal/Celery (async job processing)

# Client Options (Enterprise-Friendly)
1. Pure Web Upload/Download (most compatible)
2. Power Query (native Excel, no add-ins)
3. Office Scripts (TypeScript, replacing VBA)
4. Optional: Excel Add-in (requires IT approval)
```

## Sync Flow Design

### Upload Direction (Excel → Server)

```
1. User uploads Excel file
   ↓
2. Server extracts structured data:
   - Project metadata (sheets, settings)
   - Tasks array with UIDs
   - Dependencies map
   - Resources list
   ↓
3. Diff Engine compares:
   - Previous state (from DB)
   - New state (from Excel)
   - Generates change set
   ↓
4. Conflict Detection:
   - Check if server version > Excel version
   - Identify conflicting changes
   - Apply resolution strategy
   ↓
5. Apply Changes:
   - Update PostgreSQL
   - Log audit trail
   - Trigger notifications
```

### Download Direction (Server → Excel)

```
1. User requests latest version
   ↓
2. Server generates Excel with:
   - Latest task data
   - Embedded metadata (version, hash)
   - Change highlighting
   - Sync status indicators
   ↓
3. Smart Formula Generation:
   - Preserve user's custom columns
   - Update only managed columns
   - Maintain formula integrity
```

## Key Technical Components

### 1. Change Tracking System

```python
# Every Excel file gets embedded metadata
class ExcelMetadata:
    version: int  # Increments with each sync
    hash: str     # SHA-256 of data state
    user_id: str  
    timestamp: datetime
    sync_url: str  # API endpoint for this project

# Hidden worksheet "_SYNC_META" stores:
# - Version number
# - Last sync timestamp  
# - Project UUID
# - Column mappings
# - Change log
```

### 2. Unique Identifier Strategy

```python
# Each task gets a UUID that persists across syncs
# Stored in a hidden column in Excel

def generate_task_id():
    """
    Generate user-friendly but unique task IDs
    Format: SF-XXXX-XXXX
    """
    return f"SF-{uuid4().hex[:4].upper()}-{uuid4().hex[:4].upper()}"

# Excel formula references use these IDs, not row numbers
# Example: =SUMIF(TaskID_Range, "SF-A3B4-C5D6", Cost_Range)
```

### 3. Conflict Resolution

```python
class ConflictStrategy(Enum):
    SERVER_WINS = "server"      # Default for enterprises
    CLIENT_WINS = "client"      # User override
    MANUAL = "manual"           # Show diff, user picks
    MERGE = "merge"             # Attempt auto-merge

# Non-conflicting changes merge automatically:
# - User A updates Task 1 status
# - User B updates Task 2 duration
# Both changes apply

# Conflicts require resolution:
# - Both users change same task's date
# - Server wins by default, user notified
```

## Enterprise-Friendly Sync Options

### Option 1: Pure Web Interface (Most Compatible)

**Implementation:**
```javascript
// No Excel add-ins needed
// User manually uploads/downloads

// Upload flow:
async function uploadExcel(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId);
    
    const response = await fetch('/api/sync/upload', {
        method: 'POST',
        body: formData,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const result = await response.json();
    displaySyncResults(result);
}

// Download flow:
async function downloadLatest() {
    const response = await fetch(`/api/sync/download/${projectId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const blob = await response.blob();
    downloadFile(blob, `project_${projectId}_latest.xlsx`);
}
```

**Pros:**
- Zero IT approval needed
- Works on any system with a browser
- No security warnings

**Cons:**
- Manual process
- No real-time sync

### Option 2: Power Query Integration (Native Excel)

**Implementation:**
```m
// Power Query M Language
// Built into Excel, refreshable data connection

let
    // Configuration
    ApiUrl = "https://api.sprintforge.com/projects/",
    ProjectId = Excel.CurrentWorkbook(){[Name="ProjectId"]}[Content]{0}[Column1],
    Token = Excel.CurrentWorkbook(){[Name="ApiToken"]}[Content]{0}[Column1],
    
    // Fetch data
    Source = Web.Contents(
        ApiUrl & ProjectId & "/tasks",
        [
            Headers = [
                #"Authorization" = "Bearer " & Token,
                #"Accept" = "application/json"
            ]
        ]
    ),
    
    // Parse JSON
    JsonData = Json.Document(Source),
    
    // Convert to table
    TaskTable = Table.FromRecords(JsonData[tasks]),
    
    // Add metadata
    WithMetadata = Table.AddColumn(
        TaskTable, 
        "LastSync", 
        each DateTime.LocalNow()
    )
in
    WithMetadata

// User clicks "Refresh All" to sync
// One-way sync (download only) but enterprise-safe
```

**Pros:**
- Native Excel feature
- IT-approved in most organizations
- Can be scheduled to auto-refresh

**Cons:**
- Read-only (no upload capability)
- Requires some Power Query knowledge

### Option 3: Office Scripts (Modern Automation)

**Implementation:**
```typescript
// Office Scripts - TypeScript that runs in Excel
// Replacing VBA, more secure, cloud-enabled

interface SyncResponse {
    success: boolean;
    version: number;
    changes: Change[];
    conflicts: Conflict[];
}

async function syncWithServer(workbook: ExcelScript.Workbook): Promise<void> {
    // Get configuration
    const configSheet = workbook.getWorksheet("_CONFIG");
    const projectId = configSheet.getRange("B1").getValue() as string;
    const apiToken = configSheet.getRange("B2").getValue() as string;
    
    // Read current data
    const sheet = workbook.getWorksheet("Tasks");
    const range = sheet.getUsedRange();
    const values = range.getValues();
    
    // Detect changes
    const changes = detectChanges(workbook, values);
    
    // Call sync API
    const response = await fetch("https://api.sprintforge.com/sync", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${apiToken}`
        },
        body: JSON.stringify({
            project_id: projectId,
            version: getCurrentVersion(workbook),
            changes: changes
        })
    });
    
    // Process response
    const syncResult: SyncResponse = await response.json();
    
    if (syncResult.success) {
        applyUpdates(sheet, syncResult.changes);
        updateVersion(workbook, syncResult.version);
        
        if (syncResult.conflicts.length > 0) {
            showConflicts(workbook, syncResult.conflicts);
        }
    }
}

function detectChanges(
    workbook: ExcelScript.Workbook, 
    currentValues: (string | number | boolean)[][]
): Change[] {
    const changes: Change[] = [];
    const hashSheet = workbook.getWorksheet("_HASH");
    const previousHashes = hashSheet.getUsedRange()?.getValues() || [];
    
    // Compare each row hash
    currentValues.forEach((row, index) => {
        const currentHash = hashRow(row);
        const previousHash = previousHashes[index]?.[0];
        
        if (currentHash !== previousHash) {
            changes.push({
                row: index,
                taskId: row[0] as string,  // Assuming first column is task ID
                data: row
            });
        }
    });
    
    return changes;
}
```

**Pros:**
- Modern, Microsoft-supported
- TypeScript (type-safe)
- Cloud-compatible
- No security warnings

**Cons:**
- Requires Office 365
- Limited API access

### Option 4: Signed Excel Add-in (Advanced)

**Manifest Configuration:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:type="TaskPaneApp">
    <Id>e504fb41-a92a-4526-b101-SprintForgeSync</Id>
    <Version>1.0.0.0</Version>
    <ProviderName>SprintForge</ProviderName>
    <DefaultLocale>en-US</DefaultLocale>
    <DisplayName DefaultValue="SprintForge Sync"/>
    <Description DefaultValue="Sync your project with SprintForge"/>
    <IconUrl DefaultValue="https://sprintforge.com/icon-32.png"/>
    <HighResolutionIconUrl DefaultValue="https://sprintforge.com/icon-64.png"/>
    
    <Hosts>
        <Host Name="Workbook"/>
    </Hosts>
    
    <Requirements>
        <Sets>
            <Set Name="ExcelApi" MinVersion="1.12"/>
        </Sets>
    </Requirements>
    
    <DefaultSettings>
        <SourceLocation DefaultValue="https://sprintforge.com/addin/taskpane.html"/>
    </DefaultSettings>
    
    <Permissions>ReadWriteDocument</Permissions>
</OfficeApp>
```

**Add-in Implementation:**
```typescript
// Add-in JavaScript/TypeScript
Office.onReady((info) => {
    if (info.host === Office.HostType.Excel) {
        document.getElementById("sync-button").onclick = syncNow;
        setupAutoSync();
    }
});

async function syncNow() {
    try {
        await Excel.run(async (context) => {
            const sheet = context.workbook.worksheets.getActiveWorksheet();
            const range = sheet.getUsedRange();
            range.load("values");
            
            await context.sync();
            
            // Perform sync
            const result = await performSync(range.values);
            
            // Update Excel
            if (result.hasUpdates) {
                range.values = result.newValues;
                await context.sync();
            }
            
            showNotification(result.message);
        });
    } catch (error) {
        showError(error);
    }
}
```

**Pros:**
- Best user experience
- Real-time sync capability
- Full Excel API access

**Cons:**
- Requires IT approval
- Installation needed
- Certificate signing required

## Data Integrity & Security

### Version Control in Excel

```python
# Each sync creates a version entry
@dataclass
class SyncVersion:
    version_number: int
    sync_timestamp: datetime
    changes_made: List[Change]
    user: str
    hash_before: str
    hash_after: str
    
    def to_excel_row(self) -> List:
        """Convert to Excel row format"""
        return [
            self.version_number,
            self.sync_timestamp.isoformat(),
            len(self.changes_made),
            self.user,
            self.hash_before,
            self.hash_after
        ]

# Store in hidden sheet "_VERSION_HISTORY"
# Allows rollback if needed
```

### Audit Trail Database Schema

```sql
-- PostgreSQL audit table
CREATE TABLE sync_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    excel_version INT NOT NULL,
    server_version INT NOT NULL,
    sync_type VARCHAR(20) NOT NULL, -- 'upload' or 'download'
    changes JSONB,
    conflicts JSONB,
    resolution VARCHAR(20),
    user_id UUID NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Index for fast lookups
CREATE INDEX idx_sync_audit_project_time 
    ON sync_audit(project_id, timestamp DESC);
CREATE INDEX idx_sync_audit_user 
    ON sync_audit(user_id, timestamp DESC);
```

### Security Implementation

```python
import hashlib
import hmac
from typing import Optional
import openpyxl
import io
import re

class ExcelSecurityValidator:
    """Validate Excel files for security threats"""
    
    # Dangerous formula patterns
    DANGEROUS_FORMULAS = [
        r'=.*WEBSERVICE',
        r'=.*FILTERXML',
        r'=.*ENCODEURL',
        r'=.*CALL',
        r'=.*REGISTER',
        r'=.*EXEC',
    ]
    
    def validate_upload(self, file_bytes: bytes) -> bool:
        """
        Comprehensive validation of uploaded Excel file
        """
        # 1. File size check (prevent DOS)
        if len(file_bytes) > 50_000_000:  # 50MB limit
            raise ValueError("File exceeds 50MB limit")
        
        # 2. File type validation
        try:
            workbook = openpyxl.load_workbook(
                io.BytesIO(file_bytes),
                data_only=True,  # No macros
                keep_vba=False,  # Strip any VBA
                keep_links=False  # No external links
            )
        except Exception as e:
            raise ValueError(f"Invalid Excel file: {str(e)}")
        
        # 3. Formula security check
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value and str(cell.value).startswith('='):
                        self._validate_formula_safety(cell.value)
        
        # 4. Check for hidden sheets with suspicious names
        for sheet in workbook.worksheets:
            if sheet.sheet_state == 'hidden':
                if sheet.title.startswith('_') and sheet.title not in [
                    '_SYNC_META', '_VERSION_HISTORY', '_CONFIG'
                ]:
                    raise ValueError(f"Suspicious hidden sheet: {sheet.title}")
        
        return True
    
    def _validate_formula_safety(self, formula: str) -> None:
        """Check formula for security risks"""
        formula_upper = formula.upper()
        
        for pattern in self.DANGEROUS_FORMULAS:
            if re.search(pattern, formula_upper):
                raise ValueError(f"Dangerous formula detected: {formula[:50]}")
        
        # Check for external references
        if '!' in formula and '[' in formula:
            raise ValueError("External workbook references not allowed")

class SyncAuthentication:
    """Handle authentication for sync operations"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
    
    def generate_sync_token(self, project_id: str, user_id: str) -> str:
        """Generate time-limited sync token"""
        import time
        import json
        import base64
        
        payload = {
            'project_id': project_id,
            'user_id': user_id,
            'timestamp': int(time.time()),
            'expires': int(time.time()) + 3600  # 1 hour expiry
        }
        
        payload_json = json.dumps(payload)
        signature = hmac.new(
            self.secret_key,
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        token = base64.b64encode(
            f"{payload_json}:{signature}".encode()
        ).decode()
        
        return token
    
    def verify_sync_token(self, token: str) -> Optional[dict]:
        """Verify and decode sync token"""
        import time
        import json
        import base64
        
        try:
            decoded = base64.b64decode(token).decode()
            payload_json, signature = decoded.split(':')
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                payload_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Check expiry
            payload = json.loads(payload_json)
            if payload['expires'] < int(time.time()):
                return None
            
            return payload
            
        except Exception:
            return None
```

## Enterprise Deployment Options

### 1. SaaS with Enterprise Controls

```yaml
# enterprise-config.yaml
enterprise:
  customer: acme-corp
  settings:
    domain: acme.sprintforge.com
    region: us-east-1
    data_retention_days: 90
    audit_export:
      type: splunk
      endpoint: https://splunk.acme.com/services/collector
      token: ${SPLUNK_TOKEN}
    ip_whitelist:
      - 10.0.0.0/8
      - 172.16.0.0/12
    sso:
      provider: okta
      metadata_url: https://acme.okta.com/app/metadata
    encryption:
      at_rest: AES-256
      in_transit: TLS-1.3
      key_management: customer-managed
```

### 2. Private Cloud Deployment

```dockerfile
# Dockerfile for on-premise deployment
FROM python:3.11-slim

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Security hardening
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment configuration
ENV DEPLOYMENT_MODE=on_premise
ENV DATABASE_URL=postgresql://user:pass@postgres:5432/sprintforge
ENV REDIS_URL=redis://redis:6379
ENV S3_ENDPOINT=http://minio:9000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml for on-premise
version: '3.8'

services:
  app:
    build: .
    depends_on:
      - postgres
      - redis
      - minio
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/sprintforge
      - REDIS_URL=redis://redis:6379
      - S3_ENDPOINT=http://minio:9000
      - S3_ACCESS_KEY=${S3_ACCESS_KEY}
      - S3_SECRET_KEY=${S3_SECRET_KEY}
    ports:
      - "8000:8000"
    networks:
      - sprintforge

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=sprintforge
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - sprintforge

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - sprintforge

  minio:
    image: minio/minio
    command: server /data
    environment:
      - MINIO_ROOT_USER=${S3_ACCESS_KEY}
      - MINIO_ROOT_PASSWORD=${S3_SECRET_KEY}
    volumes:
      - minio_data:/data
    networks:
      - sprintforge

volumes:
  postgres_data:
  redis_data:
  minio_data:

networks:
  sprintforge:
    driver: bridge
```

### 3. Hybrid Deployment Mode

```python
# hybrid_sync.py
from typing import Optional, Dict, List
import requests
from dataclasses import dataclass

@dataclass
class HybridSyncConfig:
    """Configuration for hybrid cloud/on-premise sync"""
    local_db_url: str
    cloud_api_url: Optional[str] = None
    sync_sensitive_data: bool = False
    pii_fields: List[str] = None
    
class HybridSyncManager:
    """
    Manages sync between on-premise and cloud instances
    Keeps sensitive data on-premise while syncing sanitized data to cloud
    """
    
    def __init__(self, config: HybridSyncConfig):
        self.config = config
        self.local_db = PostgreSQL(config.local_db_url)
        self.pii_fields = config.pii_fields or [
            'email', 'phone', 'ssn', 'salary', 'address'
        ]
    
    def sync_to_cloud(self, project_id: str) -> Dict:
        """
        Sync sanitized project data to cloud
        """
        # Fetch local data
        project_data = self.local_db.get_project(project_id)
        
        # Sanitize sensitive information
        if not self.config.sync_sensitive_data:
            project_data = self._sanitize_data(project_data)
        
        # Send to cloud if configured
        if self.config.cloud_api_url:
            response = requests.post(
                f"{self.config.cloud_api_url}/sync",
                json={
                    'project_id': project_id,
                    'data': project_data,
                    'sync_type': 'hybrid',
                    'sanitized': not self.config.sync_sensitive_data
                },
                headers={'Authorization': f'Bearer {self._get_token()}'}
            )
            return response.json()
        
        return {'status': 'local_only', 'project_id': project_id}
    
    def _sanitize_data(self, data: Dict) -> Dict:
        """
        Remove or hash sensitive fields
        """
        import hashlib
        
        sanitized = data.copy()
        
        def hash_field(value: str) -> str:
            return hashlib.sha256(f"{value}:{self.config.local_db_url}".encode()).hexdigest()[:8]
        
        def walk_dict(d: Dict, path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                
                if key in self.pii_fields:
                    d[key] = f"REDACTED_{hash_field(str(value))}"
                elif isinstance(value, dict):
                    walk_dict(value, current_path)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            walk_dict(item, current_path)
        
        walk_dict(sanitized)
        return sanitized
```

## Performance Optimization

### Diff Algorithm for Large Projects

```python
import difflib
from typing import List, Tuple, Dict

class EfficientExcelDiff:
    """
    Efficient diff algorithm for large Excel files
    Uses rolling hash for quick comparison
    """
    
    def __init__(self):
        self.hash_cache = {}
    
    def compute_diff(
        self, 
        old_data: List[List], 
        new_data: List[List]
    ) -> Dict[str, List]:
        """
        Compute differences between two Excel data sets
        Returns: {
            'added': [...],
            'modified': [...],
            'deleted': [...]
        }
        """
        # Build hash maps for O(1) lookups
        old_map = {self._hash_row(row): (i, row) 
                  for i, row in enumerate(old_data)}
        new_map = {self._hash_row(row): (i, row) 
                  for i, row in enumerate(new_data)}
        
        # Find differences
        added = []
        modified = []
        deleted = []
        
        # Check for additions and modifications
        for hash_val, (idx, row) in new_map.items():
            if hash_val not in old_map:
                # Check if this is a modification by task ID
                task_id = row[0]  # Assuming first column is task ID
                old_row = self._find_by_task_id(old_data, task_id)
                
                if old_row:
                    modified.append({
                        'task_id': task_id,
                        'old': old_row,
                        'new': row,
                        'changes': self._get_column_changes(old_row, row)
                    })
                else:
                    added.append({'index': idx, 'data': row})
        
        # Check for deletions
        for hash_val, (idx, row) in old_map.items():
            if hash_val not in new_map:
                task_id = row[0]
                if not self._find_by_task_id(new_data, task_id):
                    deleted.append({'index': idx, 'data': row})
        
        return {
            'added': added,
            'modified': modified,
            'deleted': deleted
        }
    
    def _hash_row(self, row: List) -> str:
        """Generate hash for a row"""
        import hashlib
        row_str = '|'.join(str(cell) for cell in row)
        return hashlib.md5(row_str.encode()).hexdigest()
    
    def _find_by_task_id(self, data: List[List], task_id: str) -> Optional[List]:
        """Find row by task ID"""
        for row in data:
            if row[0] == task_id:
                return row
        return None
    
    def _get_column_changes(self, old_row: List, new_row: List) -> List[Dict]:
        """Get specific column changes"""
        changes = []
        for i, (old_val, new_val) in enumerate(zip(old_row, new_row)):
            if old_val != new_val:
                changes.append({
                    'column': i,
                    'old_value': old_val,
                    'new_value': new_val
                })
        return changes
```

### Caching Strategy

```python
from functools import lru_cache
import redis
import pickle

class SyncCache:
    """
    Multi-level caching for sync operations
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.memory_cache = {}
    
    @lru_cache(maxsize=100)
    def get_project_hash(self, project_id: str, version: int) -> str:
        """
        Get cached project hash
        L1: Memory cache (LRU)
        L2: Redis cache
        L3: Database
        """
        cache_key = f"project_hash:{project_id}:{version}"
        
        # Try Redis
        cached = self.redis.get(cache_key)
        if cached:
            return cached.decode()
        
        # Compute and cache
        hash_value = self._compute_project_hash(project_id, version)
        self.redis.setex(cache_key, 3600, hash_value)  # 1 hour TTL
        
        return hash_value
    
    def cache_diff_result(
        self, 
        project_id: str, 
        from_version: int, 
        to_version: int, 
        diff: Dict
    ) -> None:
        """Cache diff results for common version transitions"""
        cache_key = f"diff:{project_id}:{from_version}:{to_version}"
        self.redis.setex(
            cache_key, 
            900,  # 15 minutes TTL
            pickle.dumps(diff)
        )
    
    def get_cached_diff(
        self, 
        project_id: str, 
        from_version: int, 
        to_version: int
    ) -> Optional[Dict]:
        """Retrieve cached diff if available"""
        cache_key = f"diff:{project_id}:{from_version}:{to_version}"
        cached = self.redis.get(cache_key)
        return pickle.loads(cached) if cached else None
```

## Error Handling & Recovery

### Sync Failure Recovery

```python
from enum import Enum
from typing import Optional

class SyncStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CONFLICT = "conflict"

class SyncRecovery:
    """
    Handle sync failures and provide recovery mechanisms
    """
    
    def __init__(self, db, storage):
        self.db = db
        self.storage = storage
    
    async def attempt_sync_with_retry(
        self, 
        project_id: str, 
        excel_data: bytes,
        max_retries: int = 3
    ) -> Dict:
        """
        Attempt sync with exponential backoff retry
        """
        import asyncio
        
        for attempt in range(max_retries):
            try:
                # Create recovery point
                recovery_id = await self.create_recovery_point(
                    project_id, 
                    excel_data
                )
                
                # Attempt sync
                result = await self.perform_sync(project_id, excel_data)
                
                if result['status'] == SyncStatus.SUCCESS:
                    # Clean up recovery point
                    await self.delete_recovery_point(recovery_id)
                    return result
                
                elif result['status'] == SyncStatus.CONFLICT:
                    # Don't retry conflicts
                    return result
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    # Final attempt failed
                    return {
                        'status': SyncStatus.FAILED,
                        'error': str(e),
                        'recovery_id': recovery_id
                    }
        
        return {'status': SyncStatus.FAILED}
    
    async def create_recovery_point(
        self, 
        project_id: str, 
        excel_data: bytes
    ) -> str:
        """Create a recovery point for rollback"""
        import uuid
        
        recovery_id = str(uuid.uuid4())
        
        # Store current state
        current_state = await self.db.get_project_state(project_id)
        
        # Save to storage
        await self.storage.save(
            f"recovery/{recovery_id}/state.json",
            current_state
        )
        await self.storage.save(
            f"recovery/{recovery_id}/excel.xlsx",
            excel_data
        )
        
        # Record in database
        await self.db.create_recovery_point(
            recovery_id=recovery_id,
            project_id=project_id,
            created_at=datetime.utcnow()
        )
        
        return recovery_id
    
    async def rollback_to_recovery_point(
        self, 
        recovery_id: str
    ) -> bool:
        """Rollback to a previous recovery point"""
        try:
            # Retrieve recovery data
            state = await self.storage.get(
                f"recovery/{recovery_id}/state.json"
            )
            
            # Restore state
            project_id = state['project_id']
            await self.db.restore_project_state(project_id, state)
            
            # Mark as recovered
            await self.db.mark_recovery_used(recovery_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
```

## Testing Strategy

### Unit Tests for Sync Logic

```python
import pytest
from unittest.mock import Mock, patch
import openpyxl

class TestExcelSync:
    """Test suite for Excel sync functionality"""
    
    @pytest.fixture
    def sample_excel(self):
        """Create sample Excel file for testing"""
        wb = openpyxl.Workbook()
        ws = wb.active
        
        # Headers
        ws.append(['Task ID', 'Task Name', 'Start Date', 'Duration', 'Status'])
        
        # Sample data
        ws.append(['SF-0001-A1B2', 'Design Phase', '2025-01-01', 5, 'In Progress'])
        ws.append(['SF-0002-C3D4', 'Development', '2025-01-06', 10, 'Not Started'])
        
        return wb
    
    def test_detect_changes(self, sample_excel):
        """Test change detection algorithm"""
        detector = ChangeDetector()
        
        # Modify a cell
        ws = sample_excel.active
        original_values = [list(row) for row in ws.values]
        
        ws['E2'] = 'Complete'  # Change status
        modified_values = [list(row) for row in ws.values]
        
        changes = detector.detect_changes(original_values, modified_values)
        
        assert len(changes) == 1
        assert changes[0]['task_id'] == 'SF-0001-A1B2'
        assert changes[0]['column'] == 'Status'
        assert changes[0]['old_value'] == 'In Progress'
        assert changes[0]['new_value'] == 'Complete'
    
    def test_conflict_resolution(self):
        """Test conflict resolution strategies"""
        resolver = ConflictResolver()
        
        server_change = {
            'task_id': 'SF-0001-A1B2',
            'column': 'Duration',
            'value': 7
        }
        
        client_change = {
            'task_id': 'SF-0001-A1B2',
            'column': 'Duration',
            'value': 6
        }
        
        # Test server-wins strategy
        result = resolver.resolve(
            server_change, 
            client_change, 
            ConflictStrategy.SERVER_WINS
        )
        assert result['value'] == 7
        
        # Test client-wins strategy
        result = resolver.resolve(
            server_change, 
            client_change, 
            ConflictStrategy.CLIENT_WINS
        )
        assert result['value'] == 6
    
    @patch('requests.post')
    def test_sync_api_call(self, mock_post):
        """Test API sync call"""
        mock_post.return_value.json.return_value = {
            'success': True,
            'version': 42,
            'changes': []
        }
        
        client = SyncClient('https://api.sprintforge.com')
        result = client.sync(
            project_id='test-project',
            changes=[{'task_id': 'SF-0001', 'status': 'Complete'}]
        )
        
        assert result['success'] is True
        assert result['version'] == 42
        mock_post.assert_called_once()
```

## Best Practices & Recommendations

### 1. Excel File Structure

Always maintain consistent structure:
- **Visible Sheets**: Tasks, Resources, Dashboard
- **Hidden Sheets**: _SYNC_META, _VERSION_HISTORY, _CONFIG
- **Reserved Columns**: A (Task ID), B-Z (User data), AA+ (System fields)

### 2. Sync Frequency

- **Manual Sync**: Default for most users
- **Auto-sync**: Every 15 minutes for active projects
- **Real-time**: Only for enterprise with add-in

### 3. Conflict Prevention

- **Lock Mechanism**: Warn if another user is actively editing
- **Version Check**: Always verify version before applying changes
- **Atomic Updates**: Wrap changes in transactions

### 4. Performance Guidelines

- **Batch Operations**: Sync multiple changes together
- **Incremental Sync**: Only send/receive deltas
- **Compression**: Use gzip for large Excel files
- **Pagination**: Handle projects > 1000 tasks in chunks

### 5. Security Checklist

- [ ] Validate all Excel input
- [ ] Strip macros on upload
- [ ] Use time-limited tokens
- [ ] Encrypt sensitive data
- [ ] Log all sync operations
- [ ] Implement rate limiting
- [ ] Regular security audits

## Conclusion

This two-way sync architecture provides enterprise-grade synchronization between Excel and SprintForge servers while maintaining security, data integrity, and user flexibility. The multi-option approach (web, Power Query, Office Scripts, add-in) ensures compatibility across different enterprise environments and security policies.

Key advantages:
- **No macros required** (addresses enterprise security concerns)
- **Flexible deployment** (SaaS, on-premise, or hybrid)
- **Complete audit trail** (compliance ready)
- **Conflict resolution** (handles multi-user scenarios)
- **Performance optimized** (scales to large projects)

The system treats Excel as a smart client interface while maintaining the server as the source of truth, providing the best of both worlds: familiar Excel UI with modern collaboration capabilities.