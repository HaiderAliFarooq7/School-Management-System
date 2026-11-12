package com.bfhs.parent.data.repository

import com.bfhs.parent.core.Resource
import com.bfhs.parent.data.datastore.SessionManager
import com.bfhs.parent.data.local.BfhsDatabase
import com.bfhs.parent.data.network.BfhsApiService
import com.bfhs.parent.data.network.dto.FcmTokenRequestDto
import com.bfhs.parent.data.network.dto.LoginRequestDto
import com.bfhs.parent.domain.models.Parent
import com.bfhs.parent.domain.repository.AuthRepository
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val api: BfhsApiService,
    private val sessionManager: SessionManager,
    private val database: BfhsDatabase
) : AuthRepository {

    override suspend fun login(mobileNumber: String, password: String): Resource<Parent> {
        return try {
            val response = api.login(LoginRequestDto(mobileNumber, password))
            val parent = Parent(
                name = response.parentName ?: "",
                mobileNumber = response.mobileNumber ?: mobileNumber
            )
            // Drop whatever the last parent left cached before this session
            // starts. logout() clears the database, but a session can also end
            // without it — an expired token cleared by UnauthorizedInterceptor,
            // or simply a different parent signing in on a shared family phone.
            // Clearing here covers every one of those paths, so one parent can
            // never be shown another's children, attendance or fees.
            withContext(Dispatchers.IO) { database.clearAllTables() }
            sessionManager.saveSession(response.accessToken, parent.name, parent.mobileNumber)
            Resource.Success(parent)
        } catch (e: retrofit2.HttpException) {
            // 401/400 on login specifically means bad credentials; any other
            // status (or a network failure below) shows the real cause.
            val message = if (e.code() == 401 || e.code() == 400) {
                "Invalid mobile number or password"
            } else {
                e.userMessage()
            }
            Resource.Error(message)
        } catch (e: Exception) {
            Resource.Error(e.userMessage())
        }
    }

    override suspend fun logout() {
        sessionManager.clearSession()
        // Room refuses to run clearAllTables() on the main thread, and the
        // ViewModels call this straight from viewModelScope (Dispatchers.Main)
        // — so without this the Logout button crashed the app outright.
        withContext(Dispatchers.IO) { database.clearAllTables() }
    }

    override fun isLoggedIn(): Flow<Boolean> = sessionManager.token.map { !it.isNullOrBlank() }

    override fun parent(): Flow<Parent?> =
        combine(sessionManager.parentName, sessionManager.mobileNumber) { name, mobile ->
            if (name.isNullOrBlank() && mobile.isNullOrBlank()) null
            else Parent(name.orEmpty(), mobile.orEmpty())
        }

    override suspend fun registerFcmToken(token: String) {
        try {
            if (!sessionManager.tokenOnce().isNullOrBlank()) {
                api.registerFcmToken(FcmTokenRequestDto(token))
            }
        } catch (_: Exception) {
            // Token registration is best-effort; retried on next FCM token refresh.
        }
    }

    override suspend fun registerCurrentDevice() {
        // The FCM token is minted at app startup, before login, so onNewToken()
        // fires while there's no JWT and can't register. This pulls the current
        // token after the parent is signed in and registers it. Best-effort.
        try {
            if (sessionManager.tokenOnce().isNullOrBlank()) return
            val token = currentFcmToken() ?: return
            api.registerFcmToken(FcmTokenRequestDto(token))
        } catch (_: Exception) {
            // Ignored — retried on the next dashboard load or token refresh.
        }
    }

    private suspend fun currentFcmToken(): String? = suspendCancellableCoroutine { cont ->
        FirebaseMessaging.getInstance().token
            .addOnSuccessListener { token -> if (cont.isActive) cont.resume(token) }
            .addOnFailureListener { if (cont.isActive) cont.resume(null) }
    }
}
