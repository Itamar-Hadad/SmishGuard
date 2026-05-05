# SmishGuard — Android Smishing Detection App
## Full Product & Technical Plan

---

## Context

This Android application is the mobile front-end for a Final Degree Project on SMS phishing (smishing) detection. The existing project already has a trained ML pipeline (`MLsmish.py` / `NLP_smish.py`) that uses Sentence-BERT + engineered features + an ensemble model to classify SMS as `ham` or `smish`. The Android app is the user-facing product that wraps that ML model via a REST backend, passively monitors incoming SMS, and alerts users in real time. The goal is to turn the research prototype into a functional, deployable mobile security tool.

---

## 1. Product Plan

### Vision
A privacy-first, zero-friction Android security tool that silently monitors incoming SMS messages and instantly alerts users when a phishing attempt is detected — with no configuration required.

### Core User Journey
1. User installs the app → onboarding permission screen appears
2. User grants SMS + notification permissions → app starts background monitoring
3. User receives a smishing SMS → notification fires within seconds
4. User opens app → sees simple statistics (total scanned / total phishing)
5. If SMS permission ever revoked → blocking screen prompts re-grant

### Non-Goals
- No toggle to disable SMS scanning (by product decision)
- No SMS inbox viewer
- No manual message submission
- No user account / login

---

## 2. Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Android App                          │
│                                                             │
│  ┌────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │  SMS Recv  │───▶│  SMS Worker  │───▶│  API Repository │  │
│  │ (Broadcast)│    │(WorkManager) │    │  (Retrofit)     │  │
│  └────────────┘    └──────────────┘    └────────┬────────┘  │
│                                                 │           │
│  ┌────────────┐    ┌──────────────┐             │           │
│  │  Stats UI  │◀───│  ViewModel   │◀────────────┤           │
│  │ (Activity) │    │  (LiveData)  │             │           │
│  └────────────┘    └──────────────┘    ┌────────▼────────┐  │
│                                        │  Local Storage  │  │
│  ┌────────────┐                        │  (SharedPrefs   │  │
│  │Permission  │                        │  + Room DB)     │  │
│  │ Gating     │                        └─────────────────┘  │
│  └────────────┘                                             │
└─────────────────────────────────────────────────────────────┘
         │ HTTPS + TLS
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Server (Future)                   │
│     Flask/FastAPI  →  NLP_smish.py  →  smishing_detector.pkl│
│     (or Mock Server during development)                     │
└─────────────────────────────────────────────────────────────┘
```

### Key Technology Choices

| Layer | Technology | Reason |
|---|---|---|
| Language | Kotlin | Modern Android standard |
| Architecture | MVVM | Lifecycle-aware, testable |
| DI | Hilt | Official Jetpack DI |
| Networking | Retrofit 2 + OkHttp3 | Typed HTTP client |
| Background | WorkManager | Battery-friendly, survives process death |
| Local DB | Room | SQLite ORM for scan history |
| Prefs | DataStore (Proto) | Type-safe persistent settings |
| UI | ViewBinding + Material 3 | Clean, no Compose complexity needed |
| Notifications | NotificationManager + NotificationChannel | Android 8+ required |

---

## 3. Android Permission Flow

### Required Permissions

```xml
<!-- AndroidManifest.xml -->

<!-- SMS Reading (dangerous — runtime prompt required) -->
<uses-permission android:name="android.permission.RECEIVE_SMS" />
<uses-permission android:name="android.permission.READ_SMS" />

<!-- Notifications (runtime prompt on Android 13+) -->
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

<!-- Network -->
<uses-permission android:name="android.permission.INTERNET" />

<!-- Background work (declared, no runtime prompt) -->
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
```

### Permission Request Flow

```
App Launch
    │
    ▼
Check RECEIVE_SMS granted?
    ├── NO  → Show PermissionBlockingActivity (non-dismissible)
    │              → requestPermissions([RECEIVE_SMS, READ_SMS])
    │              → If denied → show rationale + "Open Settings" button
    │              → Only way out = uninstall
    └── YES → Check POST_NOTIFICATIONS (Android 13+)
                  ├── NOT GRANTED → request inline (non-blocking)
                  └── GRANTED → Launch MainActivity (home screen)
```

### Notes on Blocking Screen
- `PermissionBlockingActivity` has no back-navigation (overrides `onBackPressed`)
- "Open Settings" deep-links to `Settings.ACTION_APPLICATION_DETAILS_SETTINGS`
- On return from settings (`onResume`), re-checks permission state

---

## 4. Main Screens & User Flow

### Screen 1 — Permission Onboarding (Blocking)

**Trigger**: SMS permission not granted.

**Content**:
- App icon + name
- Headline: "SMS Access Required"
- Body: "SmishGuard protects you by monitoring incoming SMS messages for phishing attacks. This permission is required to use the app."
- Privacy note: "Messages are sent to our secure server only for analysis and are never stored."
- CTA button: "Grant Permission" → triggers runtime permission dialog
- Secondary link (if previously denied): "Open Settings"
- No dismiss / back / skip

### Screen 2 — Home / Statistics (MainActivity)

**Trigger**: SMS permission granted.

**Content**:
```
┌────────────────────────────┐
│        SmishGuard          │
│   ●  Active Protection     │
│                            │
│  ┌──────────┐ ┌──────────┐ │
│  │   1,247  │ │    3     │ │
│  │ Scanned  │ │ Threats  │ │
│  └──────────┘ └──────────┘ │
│                            │
│  [Recent alerts list]      │
│  (optional future feature) │
└────────────────────────────┘
```

**Behavior**:
- Numbers animate on load (counter animation)
- Green indicator if no threats today; orange/red if threats detected
- Pulls from Room DB (LiveData → ViewModel → UI)

### Screen 3 — Permission Revoked (Blocking, re-shown on resume)

Same as Screen 1 but with headline: "Permission Removed — App Paused"

---

## 5. Folder / Package Structure

```
app/
├── src/main/
│   ├── AndroidManifest.xml
│   ├── java/com/smishguard/
│   │   ├── di/
│   │   │   └── AppModule.kt           # Hilt: DB, Retrofit, Repo bindings
│   │   │
│   │   ├── data/
│   │   │   ├── local/
│   │   │   │   ├── AppDatabase.kt     # Room database
│   │   │   │   ├── ScanDao.kt         # DAO: insert/count/query scans
│   │   │   │   └── ScanEntity.kt      # Room entity: id, message_preview, is_phishing, timestamp
│   │   │   ├── remote/
│   │   │   │   ├── ApiService.kt      # Retrofit interface
│   │   │   │   ├── AnalysisRequest.kt # Request data class
│   │   │   │   ├── AnalysisResponse.kt# Response data class
│   │   │   │   └── MockApiService.kt  # Dev-mode fake backend
│   │   │   └── repository/
│   │   │       └── SmsAnalysisRepo.kt # Orchestrates remote + local
│   │   │
│   │   ├── receiver/
│   │   │   ├── SmsReceiver.kt         # BroadcastReceiver: RECEIVE_SMS
│   │   │   └── BootReceiver.kt        # Re-registers after device reboot
│   │   │
│   │   ├── worker/
│   │   │   └── SmsAnalysisWorker.kt   # WorkManager: calls API, saves result
│   │   │
│   │   ├── notification/
│   │   │   └── NotificationHelper.kt  # Creates channel + fires notification
│   │   │
│   │   ├── ui/
│   │   │   ├── permission/
│   │   │   │   ├── PermissionActivity.kt
│   │   │   │   └── activity_permission.xml
│   │   │   └── home/
│   │   │       ├── MainActivity.kt
│   │   │       ├── HomeViewModel.kt
│   │   │       └── activity_main.xml
│   │   │
│   │   └── SmishGuardApp.kt           # Application class (Hilt entry point)
│   │
│   └── res/
│       ├── layout/
│       ├── drawable/
│       ├── values/
│       │   ├── strings.xml
│       │   ├── colors.xml
│       │   └── themes.xml
│       └── xml/
│           └── backup_rules.xml       # Exclude SMS content from backups
```

---

## 6. Data Model

### Room Entity — `ScanEntity`

```kotlin
@Entity(tableName = "scans")
data class ScanEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val messagePreview: String,   // First 50 chars, truncated — no full message stored
    val sender: String,           // Sender number (anonymized if possible)
    val isPhishing: Boolean,
    val confidence: Float,        // 0.0–1.0 from backend
    val timestamp: Long,          // System.currentTimeMillis()
    val backendReachable: Boolean // false if mock/offline result used
)
```

### DAO — `ScanDao`

```kotlin
@Dao
interface ScanDao {
    @Insert suspend fun insert(scan: ScanEntity)
    @Query("SELECT COUNT(*) FROM scans") fun getTotalCount(): LiveData<Int>
    @Query("SELECT COUNT(*) FROM scans WHERE isPhishing = 1") fun getPhishingCount(): LiveData<Int>
    @Query("SELECT * FROM scans ORDER BY timestamp DESC LIMIT 20") fun getRecentScans(): LiveData<List<ScanEntity>>
}
```

### DataStore Keys (SharedPreferences replacement)

```kotlin
object PreferencesKeys {
    val FIRST_LAUNCH = booleanPreferencesKey("first_launch")
    val BACKEND_URL   = stringPreferencesKey("backend_url")
    val DEV_MODE      = booleanPreferencesKey("dev_mode")
}
```

---

## 7. Background SMS Listener Design

### How It Works

Android has killed persistent background services for SMS. The correct modern approach is:

```
SMS arrives
    │
    ▼
SmsReceiver (BroadcastReceiver)
    │  Extracts: sender + body from SmsMessage[]
    │  Enqueues: WorkManager one-time work
    │
    ▼
SmsAnalysisWorker (CoroutineWorker)
    │  Calls: SmsAnalysisRepo.analyze(message)
    │  On phishing:  NotificationHelper.sendAlert(preview)
    │  Always:       ScanDao.insert(result)
    │
    ▼
Result persisted to Room DB
```

### SmsReceiver

```kotlin
class SmsReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) return
        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
        val body = messages.joinToString("") { it.messageBody }
        val sender = messages.firstOrNull()?.originatingAddress ?: "Unknown"
        SmsAnalysisWorker.enqueue(context, sender, body)
    }
}
```

### SmsAnalysisWorker

```kotlin
class SmsAnalysisWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val message = inputData.getString(KEY_MESSAGE) ?: return Result.failure()
        val sender = inputData.getString(KEY_SENDER) ?: "Unknown"
        return try {
            val result = repo.analyze(message, sender)
            dao.insert(result.toEntity())
            if (result.isPhishing) NotificationHelper.sendAlert(applicationContext, result.preview)
            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) Result.retry() else Result.failure()
        }
    }
}
```

### Android Limitations to Note

| Limitation | Impact | Mitigation |
|---|---|---|
| Android 8+ BroadcastReceiver restrictions | Static receivers for SMS still work (listed in Manifest) | Declared in AndroidManifest |
| Doze mode | May delay WorkManager work | WorkManager handles this automatically |
| Battery optimization | OEM may kill workers | Prompt user to whitelist app in battery settings |
| Android 13+ notifications | POST_NOTIFICATIONS requires runtime permission | Requested inline after SMS permission |
| Background execution limits | Cannot use a persistent Service | WorkManager is the correct solution |
| Android 10+ READ_SMS scope | Cannot read message threads | Only need RECEIVE_SMS for new messages |

---

## 8. Backend API Contract

### Base URL
`https://api.smishguard.example.com/v1` (production)
`http://10.0.2.2:8000/v1` (Android emulator → localhost)

### Endpoint: Analyze Message

**Request**
```
POST /analyze
Content-Type: application/json
Authorization: Bearer <API_KEY>

{
  "message": "URGENT: Your bank account is suspended. Click http://bit.ly/abc123 to verify.",
  "sender": "+1-555-0100",        // optional, may be anonymized
  "timestamp": 1714478400000,     // epoch ms
  "client_version": "1.0.0"
}
```

**Response — Phishing Detected**
```json
{
  "is_phishing": true,
  "confidence": 0.97,
  "label": "smish",
  "signals": ["shortened_url", "urgency_words", "bank_impersonation"],
  "request_id": "req_abc123"
}
```

**Response — Safe**
```json
{
  "is_phishing": false,
  "confidence": 0.02,
  "label": "ham",
  "signals": [],
  "request_id": "req_def456"
}
```

**Error Response**
```json
{
  "error": "service_unavailable",
  "message": "Backend temporarily unavailable",
  "retry_after": 30
}
```

### Mock Backend (Development Mode)

```kotlin
class MockApiService : ApiService {
    override suspend fun analyze(request: AnalysisRequest): AnalysisResponse {
        delay(300) // simulate network latency
        val keywords = listOf("urgent", "click", "verify", "suspended", "http", "free", "win")
        val isPhishing = keywords.any { request.message.lowercase().contains(it) }
        return AnalysisResponse(
            isPhishing = isPhishing,
            confidence = if (isPhishing) 0.91f else 0.05f,
            label = if (isPhishing) "smish" else "ham",
            signals = if (isPhishing) listOf("keyword_match_mock") else emptyList(),
            requestId = UUID.randomUUID().toString()
        )
    }
}
```

### Retrofit Interface

```kotlin
interface ApiService {
    @POST("analyze")
    suspend fun analyze(@Body request: AnalysisRequest): Response<AnalysisResponse>
}
```

---

## 9. Notification Behavior

### Channel Setup (one-time, on app launch)

```kotlin
NotificationChannel(
    CHANNEL_ID = "smishguard_alerts",
    name = "Phishing Alerts",
    importance = IMPORTANCE_HIGH       // heads-up notification
).apply {
    description = "Alerts when a suspicious SMS is detected"
    enableVibration(true)
    lockscreenVisibility = Notification.VISIBILITY_PRIVATE  // hides content on lock screen
}
```

### Notification Content

```
Title: "⚠ Suspicious SMS Detected"
Body:  "A message from +1-555-XXXX may be a phishing attempt."
       [first 40 chars of message, then "..."]

Actions:
  [View Details]  → opens MainActivity
  [Dismiss]       → dismisses notification
```

**Privacy rules for notification body:**
- Sender number: show last 4 digits only (`+1-555-XXXX`)
- Message preview: max 40 characters, stripped of URLs
- Never show the full message in the notification
- Notification is `VISIBILITY_PRIVATE` (hidden on lock screen body)

### Notification ID Strategy
- Each SMS alert gets a unique notification ID (`timestamp.toInt()`)
- Prevents newer alerts from replacing older unread ones
- Max 5 active notifications (oldest dismissed automatically)

---

## 10. Statistics Logic

### Data Source
All statistics are computed from the Room database via LiveData, so the home screen always reflects live, accurate counts.

### Counters

| Stat | Query |
|---|---|
| Total Scanned | `SELECT COUNT(*) FROM scans` |
| Total Phishing | `SELECT COUNT(*) FROM scans WHERE isPhishing = 1` |

### ViewModel

```kotlin
class HomeViewModel @Inject constructor(private val dao: ScanDao) : ViewModel() {
    val totalScanned: LiveData<Int> = dao.getTotalCount()
    val phishingCount: LiveData<Int> = dao.getPhishingCount()
}
```

### Edge Cases for Stats
- Stats persist across app restarts (Room DB is persistent)
- Stats are **not** reset if permission is revoked and re-granted
- Stats are per-device and not synced to any cloud
- On fresh install: both counters show 0
- If worker fails (backend down + retries exhausted): scan is still counted as "scanned" but marked `backendReachable = false`; classified as "safe" to avoid false positives

---

## 11. Privacy & Security Notes

### Data Minimization
- Full SMS body is sent to backend for analysis, then **immediately discarded** — not stored in the backend
- Only a 50-char preview + metadata (sender, timestamp, result) is stored locally in Room DB
- Local DB is stored in app-private storage (not accessible without root)
- Android backup rules exclude the database from cloud backups

### Consent
- App is non-functional without explicit SMS permission grant
- Permission rationale screen explains exactly what data is sent and why
- No analytics, no crash reporting SDK (can add opt-in later)

### Network Security
- TLS 1.2+ enforced via OkHttp's default TLS config
- Certificate pinning recommended for production (`CertificatePinner`)
- API key stored in `local.properties` / BuildConfig, never in source control
- `android:usesCleartextTraffic="false"` in Manifest for production

### Backend Security
- Messages should NOT be logged server-side
- Rate limiting per device ID (anonymous, hashed device fingerprint)
- Request authentication via Bearer token or HMAC signature

### GDPR / Privacy Compliance
- Privacy policy required before permission grant
- Right to delete: user can clear all data via Android App Info → Clear Data
- No personal data sent beyond the SMS text and optional sender prefix

---

## 12. Edge Cases

| Edge Case | Handling |
|---|---|
| SMS permission denied on first prompt | Show blocking screen with "Open Settings" |
| SMS permission revoked after grant | `onResume` in MainActivity detects and redirects to blocking screen |
| Backend returns 500 / network timeout | WorkManager retries up to 3 times; if all fail, record scan as `backendReachable=false`, classify as safe |
| Backend slow (>10s response) | OkHttp timeout set to 10s; worker marks retry |
| Multi-part SMS (long messages) | `Telephony.Sms.Intents.getMessagesFromIntent` auto-reassembles parts; handled transparently |
| Duplicate SMS delivery | Debounce by hash of (sender + body + truncated timestamp); skip if already processed within 5s |
| Notification permission denied (Android 13+) | App continues scanning; just can't notify. Shows in-app banner on home screen instead |
| Device reboot | BootReceiver re-registers; WorkManager work survives reboot automatically |
| App in foreground when SMS arrives | Worker still fires; notification is sent as usual (user sees it immediately) |
| Very long message body | Truncate to first 500 chars before sending to backend (cost and privacy consideration) |
| Non-SMS (RCS, WhatsApp) | Not in scope; RECEIVE_SMS only covers traditional SMS |
| Low memory / worker killed | WorkManager persists pending work in its internal DB; resumes when resources available |
| Dev mode in production build | `BuildConfig.DEV_MODE` flag; Mock only used in `debug` build variant |

---

## 13. Implementation Roadmap

### Phase 1 — Foundation (Week 1–2)
- [ ] Create Android project (Kotlin, min SDK 26 / Android 8)
- [ ] Set up Hilt dependency injection
- [ ] Implement Room database (`ScanEntity`, `ScanDao`, `AppDatabase`)
- [ ] Implement DataStore for settings
- [ ] Write `SmsReceiver` + `BootReceiver` BroadcastReceivers
- [ ] Write `SmsAnalysisWorker` skeleton (WorkManager)
- [ ] Register all receivers in AndroidManifest

### Phase 2 — UI (Week 2–3)
- [ ] Build `PermissionActivity` (blocking screen, rationale, settings deep-link)
- [ ] Build `MainActivity` (statistics counters, status indicator)
- [ ] Implement `HomeViewModel` with LiveData from Room
- [ ] Apply Material 3 theme, colors, typography

### Phase 3 — Mock Backend Integration (Week 3)
- [ ] Define Retrofit `ApiService` interface + data classes
- [ ] Implement `MockApiService` with keyword-based detection
- [ ] Wire `SmsAnalysisRepo` to toggle between mock and real
- [ ] Implement `NotificationHelper` (channel creation + alert firing)
- [ ] End-to-end test with emulator using `adb shell am broadcast`

### Phase 4 — Real Backend Integration (Week 4–5)
- [ ] Deploy Flask/FastAPI backend wrapping `NLP_smish.py` + `smishing_detector.pkl`
- [ ] Replace `MockApiService` with real Retrofit implementation
- [ ] Add certificate pinning + API key auth
- [ ] Test on real device with real SMS

### Phase 5 — Polish & Hardening (Week 5–6)
- [ ] Error handling for all failure modes
- [ ] Battery optimization prompt (link to device power settings)
- [ ] Accessibility (content descriptions, large text support)
- [ ] ProGuard / R8 rules for Retrofit + Hilt
- [ ] Manual QA on 3+ Android versions (8, 12, 14)

---

## 14. Wireframes / Mockups

### Wireframe A — Permission Onboarding (Blocking Screen)

```
┌──────────────────────────────────────┐
│                                      │
│                                      │
│            🛡️ SmishGuard             │
│                                      │
│         SMS Access Required          │
│                                      │
│  ┌────────────────────────────────┐  │
│  │                                │  │
│  │  SmishGuard monitors incoming  │  │
│  │  SMS messages to protect you   │  │
│  │  from phishing attacks.        │  │
│  │                                │  │
│  │  This permission is required   │  │
│  │  to use the app.               │  │
│  │                                │  │
│  │  📡 Messages are sent to our   │  │
│  │     secure server for analysis │  │
│  │     and never stored.          │  │
│  │                                │  │
│  └────────────────────────────────┘  │
│                                      │
│   ┌──────────────────────────────┐   │
│   │      Grant SMS Permission    │   │  ← Primary CTA
│   └──────────────────────────────┘   │
│                                      │
│        Open Settings instead         │  ← Secondary (if denied)
│                                      │
│   If you don't want to grant         │
│   permission, please uninstall       │
│   the app.                           │
│                                      │
└──────────────────────────────────────┘
```

### Wireframe B — Home Statistics Screen

```
┌──────────────────────────────────────┐
│  SmishGuard                    ⋮     │
├──────────────────────────────────────┤
│                                      │
│   ● Active — Protection is ON        │  ← Green status dot
│                                      │
├──────────────────────────────────────┤
│                                      │
│  ┌─────────────────┐ ┌─────────────┐ │
│  │                 │ │             │ │
│  │     1,247       │ │      3      │ │
│  │   Messages      │ │   Threats   │ │
│  │   Scanned       │ │  Detected   │ │
│  │                 │ │             │ │
│  └─────────────────┘ └─────────────┘ │
│                                      │
│                                      │
│         Protecting since             │
│         April 30, 2026               │
│                                      │
└──────────────────────────────────────┘
```

### Wireframe C — Phishing Alert Notification

```
┌──────────────────────────────────────┐
│  SmishGuard                  just now │
│  ⚠ Suspicious SMS Detected           │
│  A message from +1-555-XXXX may be   │
│  a phishing attempt.                 │
│  ────────────────────────────────    │
│  [View Details]          [Dismiss]   │
└──────────────────────────────────────┘
```

---

## Critical Files to Create

| File | Purpose |
|---|---|
| `app/src/main/AndroidManifest.xml` | Permissions + receivers declaration |
| `data/local/ScanEntity.kt` | Room entity |
| `data/local/ScanDao.kt` | Room DAO |
| `data/local/AppDatabase.kt` | Room DB |
| `data/remote/ApiService.kt` | Retrofit interface |
| `data/remote/MockApiService.kt` | Mock backend |
| `data/repository/SmsAnalysisRepo.kt` | Business logic |
| `receiver/SmsReceiver.kt` | BroadcastReceiver for SMS |
| `worker/SmsAnalysisWorker.kt` | WorkManager worker |
| `notification/NotificationHelper.kt` | Notification utilities |
| `ui/permission/PermissionActivity.kt` | Blocking permission screen |
| `ui/home/MainActivity.kt` | Home screen |
| `ui/home/HomeViewModel.kt` | Statistics ViewModel |
| `di/AppModule.kt` | Hilt module |
| `SmishGuardApp.kt` | Application class |

## Dependencies (build.gradle)

```kotlin
// Hilt
implementation("com.google.dagger:hilt-android:2.51")
kapt("com.google.dagger:hilt-compiler:2.51")

// Room
implementation("androidx.room:room-runtime:2.6.1")
implementation("androidx.room:room-ktx:2.6.1")
kapt("androidx.room:room-compiler:2.6.1")

// WorkManager
implementation("androidx.work:work-runtime-ktx:2.9.0")

// Retrofit + OkHttp
implementation("com.squareup.retrofit2:retrofit:2.11.0")
implementation("com.squareup.retrofit2:converter-gson:2.11.0")
implementation("com.squareup.okhttp3:okhttp:4.12.0")
implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

// DataStore
implementation("androidx.datastore:datastore-preferences:1.1.1")

// ViewModel + LiveData
implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.0")
implementation("androidx.lifecycle:lifecycle-livedata-ktx:2.8.0")

// Material Design 3
implementation("com.google.android.material:material:1.12.0")

// Hilt WorkManager integration
implementation("androidx.hilt:hilt-work:1.2.0")
kapt("androidx.hilt:hilt-compiler:1.2.0")
```

## Verification Checklist

- [ ] Send test SMS via `adb shell am broadcast -a android.provider.Telephony.SMS_RECEIVED --es "pdu" ...`
- [ ] Verify WorkManager fires and calls mock backend
- [ ] Verify notification appears with correct truncated content
- [ ] Verify Room DB increments both counters correctly
- [ ] Revoke SMS permission → confirm blocking screen appears
- [ ] Kill app process → send SMS → verify still detected (WorkManager survives)
- [ ] Deny notification permission → confirm no crash, in-app banner shown
- [ ] Test on Android 8, 12, and 14
