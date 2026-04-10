Statistics Tab - Implementation Plan

Status: Planning & Implementation

Features to Implement:

A. Overview Cards
- Total secrets detected
- Legitimate secrets (not false positive)
- False positives count
- High-confidence detections (>=0.8)
- Repositories scanned count
- Average confidence score

B. By Secret Type Statistics
- Bar chart or list showing:
  - Count for each secret type
  - Repositories affected
  - Average confidence score
  - Trend (increase/decrease)

C. By Repository Statistics
- Table showing:
  - Repository name
  - Total secrets
  - Secret types breakdown (top 3)
  - Last scanned date
  - Scan status

D. Timeline/Trends (Last 30 days)
- Line chart showing detections per day
- Break down by secret type
- Daily average
- Trend indicator

E. Scan History
- Table with recent scans:
  - Scan date/time
  - Repository name
  - Commits scanned
  - Secrets found
  - Execution time
  - Status (completed/error)
- Aggregated stats:
  - Total commits scanned
  - Total secrets found
  - Total scan time

F. Top Repositories by Risk
- Ranked list:
  - Repository name
  - Secret count
  - High-confidence % 
  - Trend

UI Layout:
┌─────────────────────────────────────────┐
│ Statistics Dashboard                     │
├─────────────────────────────────────────┤
│ Overview Cards (6 cards in 3x2 grid)    │
│ ┌──────┐ ┌──────┐ ┌──────┐             │
│ │Total │ │Legit │ │False │             │
│ │ 73   │ │ 68   │ │  5   │             │
│ └──────┘ └──────┘ └──────┘             │
├─────────────────────────────────────────┤
│ Main Stats Grid (2 columns)              │
│ ┌─────────────────┐ ┌─────────────────┐ │
│ │ By Secret Type  │ │ By Repository   │ │
│ │ (Bar Chart)     │ │ (Table)         │ │
│ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────┤
│ Timeline (Full width)                   │
│ (Line Chart - Last 30 days)             │
├─────────────────────────────────────────┤
│ Scan History (Full width)               │
│ (Table with pagination)                 │
└──────────────────────────────��──────────┘

API Endpoints Needed:
GET /stats/overview
  Returns: {
    total_detections,
    legitimate_detections,
    false_positives,
    high_confidence_count,
    avg_confidence_score,
    repositories_count
  }

GET /stats/by-type
  Returns: [
    {
      secret_type,
      count,
      repositories_affected,
      avg_confidence
    }
  ]

GET /stats/by-repository
  Returns: [
    {
      repository_id,
      repository_name,
      total_secrets,
      high_confidence_count,
      types_breakdown,
      last_scanned_at,
      scan_status
    }
  ]

GET /stats/timeline?days=30
  Returns: [
    {
      date,
      count,
      by_type: { type: count }
    }
  ]

GET /stats/scan-history?limit=20&offset=0
  Returns: {
    items: [
      {
        id,
        repository_name,
        scan_date,
        commits_scanned,
        secrets_found,
        execution_time_seconds,
        status
      }
    ],
    total: count
  }

Data Models:
interface StatisticsOverview {
  total_detections: number
  legitimate_detections: number
  false_positives: number
  high_confidence_count: number
  avg_confidence_score: number
  repositories_count: number
}

interface SecretTypeStats {
  secret_type: string
  count: number
  repositories_affected: number
  avg_confidence: number
}

interface RepositoryStats {
  repository_id: number
  repository_name: string
  total_secrets: number
  high_confidence_count: number
  types_breakdown: { [type: string]: number }
  last_scanned_at: string
  scan_status: string
}

interface TimelineEntry {
  date: string
  count: number
  by_type: { [type: string]: number }
}

interface ScanHistoryItem {
  id: number
  repository_name: string
  scan_date: string
  commits_scanned: number
  secrets_found: number
  execution_time_seconds: number
  status: string
}

Components to Create:
1. StatisticsTab.tsx (main component)
2. OverviewCards.tsx (6 stat cards)
3. SecretTypeChart.tsx (bar chart or list)
4. RepositoryStats.tsx (table)
5. TimelineChart.tsx (line chart)
6. ScanHistory.tsx (table with pagination)

Libraries Needed:
- Chart.js or Recharts for charts
- Already have: React, TypeScript, CSS

Implementation Steps:
1. Create StatisticsTab component structure
2. Implement overview cards
3. Implement secret type stats
4. Implement repository stats
5. Implement timeline chart
6. Implement scan history
7. Add CSS styling
8. Test all features

Testing Checklist:
- Overview cards display correct numbers
- Secret type stats are accurate
- Repository ranking is correct
- Timeline shows trend correctly
- Scan history paginated properly
- Responsive design works
- Error handling works
- Loading states display

Performance Considerations:
- Cache stats for 5 minutes
- Lazy load charts
- Paginate scan history
- Optimize queries
- Use aggregation in backend

API Response Format Examples:

GET /stats/overview - Success (200)
{
  "total_detections": 73,
  "legitimate_detections": 68,
  "false_positives": 5,
  "high_confidence_count": 45,
  "avg_confidence_score": 0.82,
  "repositories_count": 2
}

Error (500):
{
  "detail": "Error calculating statistics",
  "status": "error"
}

GET /stats/by-type - Success (200)
[
  {
    "secret_type": "AWS_KEY",
    "count": 30,
    "repositories_affected": 2,
    "avg_confidence": 0.92
  },
  {
    "secret_type": "GITHUB_TOKEN",
    "count": 15,
    "repositories_affected": 1,
    "avg_confidence": 0.88
  }
]

GET /stats/timeline?days=30 - Success (200)
[
  {
    "date": "2026-04-01",
    "count": 5,
    "by_type": {
      "AWS_KEY": 3,
      "GITHUB_TOKEN": 2
    }
  },
  {
    "date": "2026-04-02",
    "count": 8,
    "by_type": {
      "AWS_KEY": 5,
      "SSH_KEY": 3
    }
  }
]

GET /stats/scan-history?limit=20&offset=0 - Success (200)
{
  "items": [
    {
      "id": 1,
      "repository_name": "maihongminh/Minz-chat",
      "scan_date": "2026-04-10T13:36:48",
      "commits_scanned": 10,
      "secrets_found": 71,
      "execution_time_seconds": 45,
      "status": "completed"
    }
  ],
  "total": 5,
  "total_commits_scanned": 30,
  "total_secrets_found": 73,
  "total_scan_time_seconds": 120
}

Chart Library Selection:

Recommended: Recharts
- Pros:
  * Built on React components
  * Easy to use, good documentation
  * Responsive by default
  * Good TypeScript support
  * Lightweight
- Cons:
  * Limited customization vs D3
  * Not as powerful as Chart.js for complex charts

Installation:
npm install recharts

Usage:
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'

Caching Strategy:

Frontend Caching (Recommended for this app):
- Use React state with timestamp
- Cache duration: 5 minutes (300,000 ms)
- Auto-refresh when:
  * User manually clicks Refresh button
  * Cache expires (5 minutes)
  * After scan completes
- Implementation:
  const [statsCache, setStatsCache] = useState(null)
  const [cacheTime, setCacheTime] = useState(null)
  
  const getStats = async () => {
    const now = Date.now()
    if (statsCache && now - cacheTime < 5 * 60 * 1000) {
      return statsCache
    }
    const data = await fetch('/stats/overview')
    setStatsCache(data)
    setCacheTime(now)
    return data
  }

Timeline Configuration:

Default: Last 30 days
- Show dates on X-axis
- Show count on Y-axis
- Line chart with area fill
- Hover tooltip with details
- Click legend to toggle secret types
- Auto-generate dates (today - 30 days)
- Format: YYYY-MM-DD

Scan History Pagination:

Items per page: 20
Sort: By scan_date DESC (newest first)
Pagination controls: Previous, 1-2-3..., Next
Show: "Showing X-Y of Z results"

Example:
Page 1: Items 1-20
Page 2: Items 21-40
...

Query: GET /stats/scan-history?limit=20&offset=0

Error Handling:

Frontend Error States:
1. Network Error:
   Display: "Failed to load statistics. Please try again."
   Retry button: Yes
   
2. API Error (500):
   Display: "Error loading statistics"
   Show error details in console
   Retry button: Yes
   
3. Empty Data:
   Display: "No statistics available yet"
   Show when: total_detections = 0
   
4. Partial Data Error:
   Example: Timeline fails but overview works
   Display: Show what loaded, hide failed sections
   Show warning: "Some statistics unavailable"

Retry Logic:
- Max 3 retries
- Exponential backoff: 1s, 2s, 4s
- After 3 failures: Show error message

Loading States:

Skeleton Loaders (Recommended):
- Overview cards: Gray placeholder (animate pulse)
- Charts: Chart outline with gray fill (animate)
- Tables: Row placeholders (5 rows, no content)

Implementation:
const SkeletonCard = () => (
  <div className="skeleton-card animate-pulse">
    <div className="skeleton-line"></div>
  </div>
)

CSS:
.skeleton-card {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

Loading Approach: Parallel
- Fetch all stats in parallel (Promise.all)
- Show individual loading states for each section
- Faster than sequential loading

Responsive Design:

Desktop (1200px+):
- Overview: 3 columns x 2 rows
- Main grid: 2 columns (Type stats | Repo stats)
- Timeline: Full width
- Scan history: Full width

Tablet (768px - 1199px):
- Overview: 2 columns x 3 rows
- Main grid: 1 column (stack)
- Timeline: Full width
- Scan history: Full width
- Smaller fonts and padding

Mobile (< 768px):
- Overview: 1 column x 6 rows
- Main grid: 1 column (full stack)
- Timeline: Full width, smaller chart
- Scan history: Table becomes card view
- Hide some details, show essentials only

CSS Grid:
@media (max-width: 1199px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .main-grid { grid-template-columns: 1fr; }
}

@media (max-width: 767px) {
  .stats-grid { grid-template-columns: 1fr; }
  .table-responsive { display: block; overflow-x: auto; }
}

Implementation Order:

Phase 1 (Day 1):
1. Create StatisticsTab component structure
2. Implement overview cards with skeleton loaders
3. Add basic CSS styling
4. Test with mock data

Phase 2 (Day 2):
1. Implement by-type statistics (bar chart)
2. Implement by-repository statistics (table)
3. Add error handling
4. Test API integration

Phase 3 (Day 3):
1. Implement timeline chart
2. Implement scan history table with pagination
3. Add caching logic
4. Polish styling

Phase 4 (Day 4):
1. Add responsive design
2. Optimize performance
3. Final testing
4. Bug fixes

Testing Checklist:

Overview Cards:
- Display correct numbers
- Show skeleton loaders while loading
- Handle API errors gracefully
- Update when stats change

Charts:
- Data displays correctly
- Legend toggles work
- Hover tooltips show info
- Responsive sizing
- No console errors

Tables:
- Rows display with data
- Pagination works
- Sorting works (if implemented)
- Responsive on mobile
- No layout breaks

Caching:
- Cache expires after 5 minutes
- Manual refresh clears cache
- New scan triggers refresh
- No stale data displayed

Error Handling:
- Network errors show message
- API errors show retry button
- Empty states display properly
- Partial failures handled

Responsive:
- Desktop layout correct
- Tablet layout correct
- Mobile layout correct
- No horizontal scrolling
- Text readable on all sizes

Performance Optimization:

1. Lazy Load Charts:
   - Use Suspense or dynamic import
   - Load chart library only when needed

2. Memoize Components:
   - Use React.memo for expensive components
   - Prevent unnecessary re-renders

3. Optimize API Calls:
   - Use caching (5 minutes)
   - Batch requests if possible
   - Request only needed data

4. Image/Asset Optimization:
   - No large images
   - Use CSS for icons
   - SVG for charts

5. Bundle Size:
   - Tree shake unused Recharts components
   - Keep bundle small

Example:
const StatisticsTab = React.memo(({ repositories, apiUrl }) => {
  // Component code
})

Status: Ready for implementation with detailed specifications

Last Updated: April 10, 2026
