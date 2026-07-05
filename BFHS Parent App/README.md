# BFHS Parent

Parent companion app for the BFHS multi-tenant School Management System (FastAPI backend).
Read-only by design: parents view attendance, monthly fees, extra charges, notifications and
the school profile — no editing, no payments, no downloads.

Built 1:1 from the **"Midnight Oxblood"** Claude Design handoff (dark glassmorphism, gold accent).

## Tech Stack

| Layer | Technology |
|---|---|
| Language / UI | Kotlin, Jetpack Compose, Material 3 |
| Architecture | MVVM + Repository pattern |
| DI | Hilt |
| Navigation | Navigation Compose (tab roots + pushed detail stack) |
| Network | Retrofit + OkHttp + Gson |
| Offline cache | Room |
| Preferences / JWT | DataStore Preferences |
| Push | Firebase Cloud Messaging |
| Images | Coil (static assets only — no student photos anywhere) |

- **Package:** `com.bfhs.parent` · **minSdk** 26 · **targetSdk** 35

## Project Structure

```
app/src/main/java/com/bfhs/parent/
├── core/               Resource wrapper, utils (formatters)
├── data/
│   ├── network/        Retrofit interface, DTOs, auth interceptor
│   ├── local/          Room database, entities, DAOs
│   ├── datastore/      SessionManager (JWT, parent identity, language)
│   └── repository/     Repository implementations + mappers (offline-first)
├── domain/
│   ├── models/         Domain models
│   └── repository/     Repository interfaces
├── di/                 Hilt modules
├── fcm/                FirebaseMessagingService
└── ui/
    ├── theme/          Colors, typography, dimens (design tokens)
    ├── components/     GlassCard, StatusPill, GoldButton, BottomNavBar, …
    ├── navigation/     Routes + NavGraph (incl. FCM deep links)
    ├── viewmodel/      ViewModels
    └── screens/        Splash, Login, Dashboard, StudentDetail, Attendance,
                        MonthlyFee, ExtraCharges, Notifications, Settings,
                        SchoolProfile, Language, About
```

## Build & Run

1. **Open in Android Studio** (Koala or newer). Let Gradle sync — the wrapper (Gradle 8.7,
   AGP 8.5.2, Kotlin 2.0.20) downloads automatically. Requires JDK 17.
2. **Backend URL:** `BASE_URL` in `app/build.gradle.kts`
   (`defaultConfig → buildConfigField`) is set to the production Render backend
   `https://school-management-backend-1t21.onrender.com/` (must keep the
   trailing slash). Change it only if you move the backend.
3. **Adjust the API routes** in `data/network/BfhsApiService.kt` if your FastAPI paths differ.
   Expected endpoints (all JSON, JWT Bearer auth except login):
   - `POST api/parent/login` `{mobile_number, password}` → `{access_token, token_type, parent_name, mobile_number}`
   - `GET  api/parent/students`
   - `GET  api/parent/students/{id}/attendance`
   - `GET  api/parent/students/{id}/fees`
   - `GET  api/parent/students/{id}/extra-charges`
   - `GET  api/parent/notifications`
   - `GET  api/parent/school`
   - `POST api/parent/fcm-token` `{fcm_token}`

   Field shapes live in `data/network/dto/Dtos.kt` — adjust `@SerializedName` values to match
   your FastAPI response models.
4. **Firebase (FCM):** create a Firebase project, add an Android app with package
   `com.bfhs.parent`, download `google-services.json` into `app/`. The google-services plugin
   is applied **only when that file exists**, so the project builds fine without it (push
   simply won't work until it's added).
5. Run on a device/emulator (API 26+).

Command line build:

```
gradlew.bat assembleDebug
```

## Behavior Notes

- **Auto-login:** the splash screen (2.2 s, tap to skip) routes to Dashboard when a JWT is
  stored in DataStore, otherwise to Login. A 401 from the backend simply surfaces as an error;
  logging out clears the token and the Room cache.
- **Offline:** every list screen emits the Room cache first, then refreshes from the API.
  If the network fails, cached data keeps the app fully viewable.
- **FCM payloads:** send *data* messages with keys `type` (`absent` | `fee_reminder` |
  `announcement`), `title`, `body`, and optional `student_id`. Tapping the notification opens
  the matching screen (Attendance / Monthly Fee / Notices tab). Channels: attendance alerts,
  fee reminders, school announcements.
- **Language:** English / اردو via Android per-app locales (`values-ur/`), persisted across
  restarts. Core labels are translated; per the design note, the full Urdu pass is a future
  update.
- **POST_NOTIFICATIONS:** on Android 13+ the permission must be granted by the user
  (declared in the manifest; request UX can be added later).

## Design Fidelity

`ui/theme/` holds the handoff's exact tokens (colors, gradients, type scale, spacing, radii).
One deliberate note: the dashboard card shows *Class · S/O Father* as its second line, exactly
as the design prototype does; the registration number is part of the `Student` model and API
contract but is not rendered on the card, since the design is the source of truth.
