#  Frontend Implementation Plan

## Overview
Detailed implementation plan for bot-scanGit frontend screens.

---

## 1.  Repositories Screen (DONE)

###  Status: Completed & Working

### Features Implemented:
-  List all repositories with cards
-  Show repository metadata:
  - Repository name
  - URL (clickable link to GitHub)
  - Scan status (scanning/completed)
  - Secrets found count
  - Last scanned date
-  Add repository from GitHub
  - Input repo name (owner/repo format)
  - Auto scan on add
  - Show scan results dialog
-  Scan trending repositories
  - Fetch and scan popular GitHub repos
-  Manual scan button
  - Re-scan existing repository
  - Show loading state
-  Delete repository
  - Remove from tracking with confirmation

### UI Components:
- Header section with refresh button
- Add repo form (input + button)
- Trending repos button
- Repository cards grid
- Status badges (scanning/completed)
- Action buttons (Scan, Delete)

### API Endpoints Used:
```
GET    /repos/                              - List all repos
POST   /scan/repository-from-github         - Add & scan repo
POST   /scan/repository/{id}                - Rescan repo
DELETE /repos/{id}                          - Delete repo
POST   /scan/trending                       - Scan trending repos
```

### Data Model:
```typescript
interface Repository {
  id: number
  name: string
  url: string
  scan_status: 'scanning' | 'completed'
  secrets_found: number
  last_scanned_at?: string
}
```

---

## 2.  Detections Screen (IN PROGRESS)

###  Status: Planning & Implementation

### Features to Implement:

#### A. Detection List View
- [ ] Table/list of all detected secrets
- [ ] Columns:
  - Secret Type (AWS Keys, GitHub Tokens, etc.)
  - Confidence Score (0-1, color-coded)
  - File Path (where secret found)
  - Repository (which repo)
  - Commit Hash (which commit, link to GitHub)
  - Detected At (timestamp)
  - Status (legitimate/false positive)
- [ ] Pagination (20-50 items per page)
- [ ] Sorting by:
  - Confidence (high to low)
  - Date (newest first)
  - Secret type

#### B. Filtering System
- [ ] Filter by repository (dropdown)
- [ ] Filter by secret type (checkboxes):
  - AWS Keys
  - Google API Keys
  - OpenAI Keys
  - Claude Keys
  - GitHub Tokens
  - Slack Tokens
  - SSH Private Keys
  - Database Credentials
  - High-Entropy Strings
- [ ] Filter by confidence threshold (slider 0-1)
- [ ] Hide/Show false positives (toggle)
- [ ] Search by file path

#### C. Detection Detail View
- [ ] Modal or side panel showing:
  - Full secret details
  - File path
  - Line number
  - Commit hash & message
  - Repository name & link
  - Detected timestamp
  - Confidence score (large)
  - Secret type
- [ ] Actions:
  - Copy details
  - Open in GitHub
  - Mark as false positive
  - Remove false positive mark

#### D. False Positive Management
- [ ] Mark detection as false positive with reason (dropdown/input)
- [ ] Remove false positive marking
- [ ] Show false positive count
- [ ] Option to exclude false positives from list

#### E. Quick Stats
- [ ] Total detections count
- [ ] High-confidence detections count (≥ 0.8)
- [ ] False positives count
- [ ] Breakdown by secret type (mini chart/list)

### UI Design:
```

  Detections                    Filters 

 Filters Panel (Sidebar)                  
  Repository: [All]                      
  Secret Type: [AWS] [GitHub] [All]     
  Confidence: [0.5  1.0]         
  Show false positives: [Toggle]         
  Search: [_______________]              

 Quick Stats                              
 Total: 73  High-Conf: 45  False-Pos: 5  

 Detection List (Table)                   
 TypeConfidenceFileRepoCommitDate  
 AWS  0.95   .envMinza1b2cNow   
 GH   0.87   config.pySFUd3e4f1h  
 SSH  0.72   key.pemSFUg5h6i2h    

```

### API Endpoints to Use:
```
GET    /detections/                         - List detections with filters
GET    /detections/{id}                     - Get detail
PATCH  /detections/{id}                     - Update (mark false positive)
Query parameters:
  ?repository_id=1
  ?secret_type=aws_key
  ?min_confidence=0.8
  ?exclude_false_positives=true
```

### Data Model:
```typescript
interface Detection {
  id: number
  repository_id: number
  commit_id: number
  file_path: string
  secret_type: string
  secret_pattern?: string
  matched_value?: string
  line_number?: number
  confidence_score: number  // 0.0 - 1.0
  is_false_positive: boolean
  remediation_status: string
  detected_at: string  // ISO datetime
  created_at: string
  updated_at: string
}

interface DetectionFilter {
  repositoryId?: number
  secretType?: string
  minConfidence?: number
  excludeFalsePositives?: boolean
  searchPath?: string
  page?: number
  pageSize?: number
}
```

### Implementation Steps:
1. Create DetectionsPage component
2. Implement filter sidebar
3. Fetch & list detections
4. Add filtering logic
5. Detail modal/panel
6. Mark false positive functionality
7. Quick stats display
8. Styling & polish

---

## 3.  Statistics Screen (TODO)

###  Status: Planned for Future

### Features to Implement:

#### A. Overview Cards
- Total secrets detected
- Legitimate secrets
- False positives
- Repositories scanned
- Average confidence score

#### B. By Secret Type
- Count for each secret type
- Bar chart or list
- Repositories affected per type
- Avg confidence per type

#### C. By Repository
- Table with:
  - Repository name
  - Total secrets
  - Types breakdown
  - Last scanned
  - Scan status
- Sortable columns

#### D. Timeline/Trends
- Line chart: Detections over last 30 days
- Break down by secret type
- Daily average

#### E. Scan History
- List of recent scans
- Scan date & time
- Repository name
- Commits scanned
- Secrets found
- Execution time
- Status (completed/error)

#### F. Aggregated Stats
- Total commits scanned
- Total secrets found
- Total scan time
- Average secrets per scan

### UI Design:
```

  Statistics                         

 Overview Cards                        
     
 Total  Legit  False   Avg   
  73     68      5    0.78   
     

 By Secret Type                        
 AWS Keys: 30 (Repos: 2, Avg: 0.92)  
 GitHub: 15 (Repos: 1, Avg: 0.88)    
 SSH Keys: 10 (Repos: 2, Avg: 0.85)  

 Trend (Last 30 Days)                  
 [Line Chart]                          

 By Repository                         
 Minz-chat: 71 secrets                 
 SFU_Server: 2 secrets                 

```

### API Endpoints:
```
GET    /stats/overview                      - Overview metrics
GET    /stats/by-type                       - By secret type
GET    /stats/by-repository                 - By repository
GET    /stats/timeline                      - Timeline data
GET    /stats/scan-history                  - Recent scans
```

### Implementation Steps:
1. Create StatisticsPage component
2. Fetch overview data
3. Create chart components (line, bar)
4. Display by-type stats
5. Display by-repo stats
6. Timeline visualization
7. Scan history table
8. Styling

---

##  Development Priority

### Phase 1 (Current):  Done
- [x] Repositories screen

### Phase 2 (Next):  In Progress
- [ ] Detections screen - Full implementation

### Phase 3 (Future):  Planned
- [ ] Statistics screen

---

##  Technical Notes

### Frontend Tech Stack:
- React 18 + TypeScript
- Vite (dev server on port 5173)
- CSS (no external framework initially)
- Fetch API for HTTP requests

### State Management:
- React hooks (useState, useEffect)
- Local component state
- Consider adding Context API if needed

### API Base URL:
```
Development: http://localhost:8000/api/v1
```

### Code Structure:
```
frontend/src/
 App.tsx                 (main app)
 components/
    RepositoriesTab.tsx (or inline in App)
    DetectionsTab.tsx
    StatisticsTab.tsx
    Common/
        Loading.tsx
        Error.tsx
        Empty.tsx
 types/
    repository.ts
    detection.ts
    statistics.ts
 services/
    api.ts            (API calls)
    filters.ts        (filter logic)
 App.css
 index.css
```

---

##  Styling Guidelines

### Colors (from existing):
- Primary: Blue (#3b82f6)
- Success: Green (#10b981)
- Error: Red (#ef4444)
- Warning: Yellow (#f59e0b)
- Background: Light gray/white

### Component Spacing:
- Cards: 1rem padding
- Section gaps: 2rem
- Grid columns: responsive (1-3 cols)

### Responsive Design:
- Mobile: 1 column
- Tablet: 2 columns
- Desktop: 3+ columns

---

##  Checklist

### Repositories Screen:
- [x] List view
- [x] Add repository form
- [x] Scan buttons
- [x] Delete functionality
- [x] Status display
- [x] Error handling

### Detections Screen:
- [ ] List view with table
- [ ] Filtering system
- [ ] Detail modal
- [ ] False positive marking
- [ ] Quick stats
- [ ] Search functionality
- [ ] Pagination
- [ ] Error handling

### Statistics Screen:
- [ ] Overview cards
- [ ] By-type stats
- [ ] By-repo stats
- [ ] Timeline chart
- [ ] Scan history
- [ ] Aggregated metrics

---

**Last Updated**: April 10, 2026
**Version**: 1.0
